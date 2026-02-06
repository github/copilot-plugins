# Observability Patterns -- .NET 9

## 1. Logging Decision Tree

| Factor | Built-in (`Microsoft.Extensions.Logging`) | Serilog |
|---|---|---|
| **Startup complexity** | Zero config, included in Host | NuGet packages + `UseSerilog()` wire-up |
| **Structured logging** | Supported via message templates | First-class; richer destructuring (`@`) |
| **Source-generated perf** | `[LoggerMessage]` -- zero-alloc | No equivalent; uses `MessageTemplate` parse cache |
| **Sink ecosystem** | Console, Debug, EventSource, OTLP | 100+ sinks (Seq, Elasticsearch, async wrappers) |
| **Enrichment** | Manual via `BeginScope` | Built-in enrichers (Machine, Thread, Correlation) |
| **Filtering at runtime** | `appsettings.json` reload | `LoggingLevelSwitch` -- change without restart |
| **OpenTelemetry export** | `AddOpenTelemetry()` on `ILoggingBuilder` | `Serilog.Sinks.OpenTelemetry` or bridge via `ILogger` |
| **Recommendation** | Default choice for new .NET 9 services | Choose when you need sink variety or advanced enrichment |

## 2. Built-in Microsoft.Extensions.Logging

Use source-generated `[LoggerMessage]` for hot-path logging. The compiler emits zero-allocation code that skips string interpolation when the log level is disabled.

```csharp
using Microsoft.Extensions.Logging;

public static partial class LogMessages
{
    [LoggerMessage(Level = LogLevel.Information, Message = "Order {OrderId} placed by {CustomerId}, total {Total}")]
    public static partial void OrderPlaced(ILogger logger, Guid orderId, string customerId, decimal total);

    [LoggerMessage(Level = LogLevel.Warning, Message = "Payment retry {Attempt} for order {OrderId}")]
    public static partial void PaymentRetry(ILogger logger, int attempt, Guid orderId);

    [LoggerMessage(Level = LogLevel.Error, Message = "Order processing failed for {OrderId}")]
    public static partial void OrderFailed(ILogger logger, Guid orderId, Exception exception);
}
```

Inject `ILogger<T>` and use scopes to attach contextual properties to every log entry within a block:

```csharp
using Microsoft.Extensions.Logging;

public class OrderService(ILogger<OrderService> logger)
{
    public async Task ProcessAsync(Order order, CancellationToken ct)
    {
        using (logger.BeginScope(new Dictionary<string, object>
        {
            ["OrderId"] = order.Id,
            ["CustomerId"] = order.CustomerId
        }))
        {
            LogMessages.OrderPlaced(logger, order.Id, order.CustomerId, order.Total);
            // All logs inside this block carry OrderId and CustomerId.
        }
    }
}
```

## 3. Serilog Setup

When you need async sinks, enrichment pipelines, or sinks not available in the built-in stack, wire Serilog as the provider.

```csharp
using Serilog;
using Serilog.Events;
using Serilog.Formatting.Compact;

// Program.cs
Log.Logger = new LoggerConfiguration()
    .MinimumLevel.Override("Microsoft.AspNetCore", LogEventLevel.Warning)
    .Enrich.FromLogContext()
    .Enrich.WithMachineName()
    .Enrich.WithThreadId()
    .Enrich.WithProperty("Service", "OrderApi")
    .WriteTo.Console(new RenderedCompactJsonFormatter())
    .WriteTo.Async(a => a.File(
        path: "logs/order-api-.log",
        rollingInterval: RollingInterval.Day,
        retainedFileCountLimit: 14,
        formatter: new RenderedCompactJsonFormatter()))
    .CreateLogger();

var builder = WebApplication.CreateBuilder(args);
builder.Host.UseSerilog();
```

Key packages for .NET 9:

```text
Serilog.AspNetCore
Serilog.Enrichers.Environment
Serilog.Enrichers.Thread
Serilog.Formatting.Compact
Serilog.Sinks.Async
Serilog.Sinks.Console
Serilog.Sinks.File
```

Serilog bridges into `ILogger<T>` so all framework and library logs flow through the same pipeline. No dual-logging.

## 4. OpenTelemetry Integration

Full setup covering traces, metrics, and logs exported via OTLP. Works with Jaeger, Grafana Tempo, Prometheus, or any OTLP-compatible backend.

```csharp
// Program.cs
using OpenTelemetry.Logs;
using OpenTelemetry.Metrics;
using OpenTelemetry.Resources;
using OpenTelemetry.Trace;

var builder = WebApplication.CreateBuilder(args);

var serviceName = "OrderApi";
var serviceVersion = "1.0.0";

var resourceBuilder = ResourceBuilder.CreateDefault()
    .AddService(serviceName: serviceName, serviceVersion: serviceVersion);

// --- Traces ---
builder.Services.AddOpenTelemetry()
    .ConfigureResource(r => r.AddService(serviceName, serviceVersion))
    .WithTracing(tracing =>
    {
        tracing
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddEntityFrameworkCoreInstrumentation()
            .AddSource("OrderApi.Commands")   // custom ActivitySource name
            .SetSampler(new ParentBasedSampler(new TraceIdRatioBasedSampler(0.1))) // 10% in prod
            .AddOtlpExporter();               // defaults to http://localhost:4317
    })
    .WithMetrics(metrics =>
    {
        metrics
            .AddAspNetCoreInstrumentation()
            .AddHttpClientInstrumentation()
            .AddRuntimeInstrumentation()
            .AddMeter("OrderApi.Metrics")      // custom Meter name
            .AddOtlpExporter();
    });

// --- Logs (built-in provider route) ---
builder.Logging.AddOpenTelemetry(logging =>
{
    logging.SetResourceBuilder(resourceBuilder);
    logging.IncludeScopes = true;
    logging.IncludeFormattedMessage = true;
    logging.AddOtlpExporter();
});
```

Custom instrumentation with the `Activity` API (the .NET native span):

```csharp
using System.Diagnostics;
using System.Diagnostics.Metrics;

public class OrderCommandHandler
{
    private static readonly ActivitySource Source = new("OrderApi.Commands");
    private static readonly Meter Meter = new("OrderApi.Metrics");
    private static readonly Counter<long> OrdersCreated = Meter.CreateCounter<long>("orders.created");

    public async Task<Guid> Handle(CreateOrderCommand cmd, CancellationToken ct)
    {
        using var activity = Source.StartActivity("CreateOrder", ActivityKind.Internal);
        activity?.SetTag("order.customer_id", cmd.CustomerId);

        // ... business logic ...

        OrdersCreated.Add(1, new KeyValuePair<string, object?>("region", cmd.Region));
        activity?.SetTag("order.id", orderId.ToString());
        return orderId;
    }
}
```

## 5. Correlation IDs

Propagate a single correlation ID across HTTP boundaries, MediatR pipeline, and log output.

```csharp
using System.Diagnostics;
using MediatR;
using Microsoft.Extensions.Logging;

// Middleware -- reads or generates X-Correlation-Id
public class CorrelationIdMiddleware(RequestDelegate next)
{
    private const string Header = "X-Correlation-Id";

    public async Task InvokeAsync(HttpContext context)
    {
        if (!context.Request.Headers.TryGetValue(Header, out var correlationId))
        {
            correlationId = Guid.NewGuid().ToString();
        }

        context.Items["CorrelationId"] = correlationId.ToString();
        Activity.Current?.SetTag("correlation.id", correlationId!);

        using (context.RequestServices.GetRequiredService<ILogger<CorrelationIdMiddleware>>()
            .BeginScope(new Dictionary<string, object> { ["CorrelationId"] = correlationId.ToString()! }))
        {
            context.Response.Headers[Header] = correlationId;
            await next(context);
        }
    }
}

// MediatR behavior -- pushes correlation into every handler's log scope
public class CorrelationBehavior<TReq, TRes>(
    IHttpContextAccessor accessor,
    ILogger<CorrelationBehavior<TReq, TRes>> logger) : IPipelineBehavior<TReq, TRes>
    where TReq : notnull
{
    public async Task<TRes> Handle(TReq request, RequestHandlerDelegate<TRes> next, CancellationToken ct)
    {
        var correlationId = accessor.HttpContext?.Items["CorrelationId"]?.ToString() ?? "N/A";
        using (logger.BeginScope(new Dictionary<string, object> { ["CorrelationId"] = correlationId }))
        {
            return await next();
        }
    }
}
```

Register in `Program.cs`:

```csharp
app.UseMiddleware<CorrelationIdMiddleware>();
builder.Services.AddHttpContextAccessor();
builder.Services.AddTransient(typeof(IPipelineBehavior<,>), typeof(CorrelationBehavior<,>));
```

## 6. Health Checks

Separate liveness (process is running) from readiness (dependencies are reachable). Kubernetes probes map directly to these endpoints.

```csharp
using Microsoft.Extensions.Diagnostics.HealthChecks;

// Program.cs
builder.Services
    .AddHealthChecks()
    .AddDbContextCheck<AppDbContext>(
        name: "database",
        tags: ["readiness"])
    .AddCheck("self", () => HealthCheckResult.Healthy(), tags: ["liveness"]);

app.MapHealthChecks("/health/live", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("liveness")
});

app.MapHealthChecks("/health/ready", new HealthCheckOptions
{
    Predicate = check => check.Tags.Contains("readiness"),
    ResponseWriter = WriteResponse
});

// Structured JSON response for readiness
static Task WriteResponse(HttpContext context, HealthReport report)
{
    context.Response.ContentType = "application/json";
    var result = new
    {
        status = report.Status.ToString(),
        checks = report.Entries.Select(e => new
        {
            name = e.Key,
            status = e.Value.Status.ToString(),
            duration = e.Value.Duration.TotalMilliseconds
        })
    };
    return context.Response.WriteAsJsonAsync(result);
}
```

Packages:

```text
Microsoft.Extensions.Diagnostics.HealthChecks
Microsoft.Extensions.Diagnostics.HealthChecks.EntityFrameworkCore
```

---

**Trade-off summary**: Start with built-in logging and `[LoggerMessage]` source generation. Add Serilog only when you need its sink ecosystem or enrichment pipeline. Wire OpenTelemetry regardless of the logging provider -- traces and metrics are independent concerns and OTLP export is the same either way.
