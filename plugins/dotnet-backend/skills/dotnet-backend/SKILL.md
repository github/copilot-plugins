---
name: dotnet-backend
description: Comprehensive guidance for building, architecting, and modernizing C# .NET backend applications. Use when user wants to create a new C# API, refactor an existing .NET backend, choose an architecture pattern (Clean Architecture, Vertical Slice Architecture, Modular Monolith), apply design patterns, design REST APIs, implement data access with EF Core or Dapper, set up CQRS with MediatR, apply Domain-Driven Design (DDD), plan testing strategies, add real-time communication with SignalR, configure resilience with Polly, handle authentication and authorization, manage database migrations, or modernize a legacy .NET application. Trigger phrases include "build a C# API", "create a .NET backend", "refactor my .NET app", "which architecture pattern should I use", "Clean Architecture vs Vertical Slice", "set up MediatR", "EF Core repository pattern", "should I use DDD", "add SignalR to my API", "Polly retry policy", "ProblemDetails error handling", "Modular Monolith vs microservices", "scaffold a dotnet project", "migrate my .NET Framework app", "FluentValidation pipeline", "background jobs in .NET", "API versioning in ASP.NET", "how to structure a .NET solution", and any question about C# backend architecture, patterns, or best practices.
---

# .NET Backend

## Purpose

.NET Backend is a decision-tree guide for building and modernizing C# backend applications on .NET 9. Rather than prescribing a single "correct" approach, this skill presents trade-offs for architecture patterns, data access strategies, testing approaches, and cross-cutting concerns so you can choose what fits your context. Every recommendation includes the *why* alongside the *how*.

## When to Use This Skill

Activate this skill when the user:

- Wants to build a new C# backend, Web API, or service from scratch
- Needs to choose between architecture patterns (Clean Architecture, Vertical Slice, Modular Monolith)
- Asks about CQRS, MediatR, DDD, or domain modeling
- Wants guidance on data access (EF Core, Dapper, or both)
- Needs to add error handling, validation, auth, or observability to a .NET API
- Is refactoring or modernizing an existing .NET application
- Asks about real-time communication (SignalR), background processing, or resilience
- Requests help structuring a .NET solution or choosing between Minimal APIs and Controllers

## Quick Start Workflow

Scaffold a basic .NET 9 Web API project:

```bash
# Create solution and API project
dotnet new sln -n MyApp
dotnet new webapi -n MyApp.Api --use-minimal-apis
dotnet sln add MyApp.Api

# Add class libraries for layered structure
dotnet new classlib -n MyApp.Application
dotnet new classlib -n MyApp.Domain
dotnet new classlib -n MyApp.Infrastructure
dotnet sln add MyApp.Application MyApp.Domain MyApp.Infrastructure

# Wire up project references
dotnet add MyApp.Api reference MyApp.Application
dotnet add MyApp.Application reference MyApp.Domain
dotnet add MyApp.Infrastructure reference MyApp.Application
dotnet add MyApp.Api reference MyApp.Infrastructure

# Install foundational NuGet packages
dotnet add MyApp.Api package Serilog.AspNetCore
dotnet add MyApp.Api package Asp.Versioning.Http
dotnet add MyApp.Application package MediatR
dotnet add MyApp.Application package FluentValidation.DependencyInjectionExtensions
dotnet add MyApp.Infrastructure package Microsoft.EntityFrameworkCore.SqlServer
dotnet add MyApp.Infrastructure package Microsoft.EntityFrameworkCore.Design
```

Adapt the project count and references to your chosen architecture (see Section 4).

## Architecture Decision Tree

Choose your architecture based on team size, domain complexity, and how you expect the system to evolve.

| Factor | Clean Architecture | Vertical Slice | Modular Monolith |
|--------|-------------------|----------------|------------------|
| **Core idea** | Strict layer separation; domain at center | Feature cohesion; each slice owns its full stack | Independent modules behind explicit boundaries |
| **Best when** | Large team, complex domain, long-lived product | Small-to-mid team, feature-oriented delivery | You want service boundaries without distributed infra |
| **Trade-off** | More abstractions, indirection | Less reuse across slices, possible duplication | Module boundary discipline required |
| **Evolves toward** | Stays monolith or extracts bounded contexts | Stays monolith or splits slices into services | Breaks modules into microservices when ready |
| **Stack file** | `stacks/clean-architecture.md` | `stacks/vertical-slice.md` | `stacks/modular-monolith.md` |

**Decision guide:**
1. *Greenfield CRUD app with a small team?* Start with Vertical Slice. Low ceremony, ship fast.
2. *Complex domain with deep business logic?* Clean Architecture gives you isolated domain tests and clear dependency direction.
3. *Multiple bounded contexts that may become services later?* Modular Monolith lets you draw service boundaries now without paying the distributed-systems tax yet.

## Core Tech Stack (Shared Foundation)

All architectures share this foundation on .NET 9:

| Concern | Choice | Notes |
|---------|--------|-------|
| **Runtime** | .NET 9 | Current release; LTS (.NET 8) also viable |
| **CQRS** | MediatR | Pipeline behaviors for cross-cutting concerns |
| **Validation** | FluentValidation | API/pipeline input validation |
| **Data (primary)** | EF Core 9 | ORM for 90% of data access |
| **Data (escape hatch)** | Dapper | Raw SQL for performance-critical queries |
| **Error handling** | ProblemDetails (RFC 9457) | Global exception middleware |
| **Logging** | Serilog *or* Microsoft.Extensions.Logging | Both integrate with OpenTelemetry |
| **Resilience** | Polly v8 | Via Microsoft.Extensions.Http.Resilience |
| **API versioning** | Asp.Versioning | URL segment strategy |
| **Auth** | Policy-based authorization | Assumes external IdP |
| **Real-time** | SignalR | Strongly-typed hubs |

## API Style Decision

.NET 9 supports two first-class API styles. Neither is universally better.

| Consideration | Minimal APIs | Controllers |
|---------------|-------------|-------------|
| **Boilerplate** | Less ceremony, lambda-based | More structure, class-based |
| **Discoverability** | Endpoints defined in code; needs grouping discipline | Conventional routing; easy to browse |
| **Filters/middleware** | Endpoint filters (newer API) | Action filters, model binding (mature) |
| **OpenAPI** | Built-in with `WithOpenApi()` | Swashbuckle or NSwag |
| **Best for** | Small APIs, microservices, vertical slices | Large APIs, teams familiar with MVC, complex model binding |
| **Testability** | `WebApplicationFactory` works for both | Same |

```csharp
// using MediatR;
// using Microsoft.AspNetCore.Mvc;

// Minimal API example
app.MapGet("/api/v1/orders/{id}", async (int id, ISender sender) =>
{
    var order = await sender.Send(new GetOrderQuery(id));
    return Results.Ok(order);
})
.WithName("GetOrder")
.WithOpenApi();

// Controller equivalent
[ApiController]
[Route("api/v1/[controller]")]
public class OrdersController(ISender sender) : ControllerBase
{
    [HttpGet("{id}")]
    public async Task<IActionResult> Get(int id)
    {
        var order = await sender.Send(new GetOrderQuery(id));
        return Ok(order);
    }
}
```

## Data Access Strategy

### EF Core as the Primary ORM

EF Core 9 is the default for all data access. DbContext already implements both the Unit of Work and Repository patterns. **Do not wrap DbContext in a custom repository layer** -- it adds indirection without meaningful benefit in most applications.

```csharp
// using MediatR;
// using Microsoft.EntityFrameworkCore;

// Direct DbContext injection -- no repository wrapper needed
public class GetOrderQueryHandler(AppDbContext db)
    : IRequestHandler<GetOrderQuery, OrderDto>
{
    public async Task<OrderDto> Handle(GetOrderQuery request, CancellationToken ct)
    {
        var order = await db.Orders
            .Include(o => o.Items)
            .Where(o => o.Id == request.Id)
            .Select(o => new OrderDto(o.Id, o.Status, o.Items.Count))
            .FirstOrDefaultAsync(ct)
            ?? throw new NotFoundException(nameof(Order), request.Id);

        return order;
    }
}
```

### Dapper Escape Hatch

When EF Core's query translation is too slow or you need hand-tuned SQL, use Dapper alongside EF Core. Inject `AppDbContext` and use `.Database.GetDbConnection()` to get the underlying connection so both share the same connection pool.

```csharp
// using Dapper;
// using Microsoft.EntityFrameworkCore;

// Performance-critical reporting query using Dapper
public class GetSalesReportHandler(AppDbContext db)
    : IRequestHandler<GetSalesReportQuery, SalesReport>
{
    public async Task<SalesReport> Handle(GetSalesReportQuery request, CancellationToken ct)
    {
        var connection = db.Database.GetDbConnection();

        const string sql = """
            SELECT Category, SUM(Amount) as Total, COUNT(*) as Count
            FROM Orders
            WHERE OrderDate >= @From AND OrderDate <= @To
            GROUP BY Category
            ORDER BY Total DESC
            """;

        var results = await connection.QueryAsync<CategorySales>(sql, new
        {
            From = request.FromDate,
            To = request.ToDate
        });

        return new SalesReport(results.ToList());
    }
}
```

## CQRS with MediatR

Separate reads (queries) from writes (commands). MediatR pipeline behaviors handle cross-cutting concerns without polluting handler logic.

### Command / Query Separation

```csharp
// using MediatR;

// Command -- changes state, returns minimal result
public record CreateOrderCommand(string CustomerId, List<OrderItemDto> Items)
    : IRequest<int>;

// Query -- reads state, returns projection
public record GetOrderQuery(int Id) : IRequest<OrderDto>;
```

### Pipeline Behaviors for Cross-Cutting Concerns

```csharp
// using FluentValidation;
// using MediatR;
// using System.Diagnostics;

// Validation behavior -- runs FluentValidation before every handler
public class ValidationBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        if (!validators.Any()) return await next();

        var context = new ValidationContext<TRequest>(request);
        var failures = (await Task.WhenAll(
                validators.Select(v => v.ValidateAsync(context, ct))))
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .ToList();

        if (failures.Count > 0)
            throw new ValidationException(failures);

        return await next();
    }
}

// Logging behavior
public class LoggingBehavior<TRequest, TResponse>(
    ILogger<LoggingBehavior<TRequest, TResponse>> logger)
    : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken ct)
    {
        var name = typeof(TRequest).Name;
        logger.LogInformation("Handling {RequestName}", name);

        var sw = Stopwatch.StartNew();
        var response = await next();
        sw.Stop();

        logger.LogInformation("Handled {RequestName} in {ElapsedMs}ms", name, sw.ElapsedMilliseconds);
        return response;
    }
}
```

### DI Registration

```csharp
services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(typeof(CreateOrderCommand).Assembly);
    cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
    cfg.AddOpenBehavior(typeof(LoggingBehavior<,>));
});
```

## Error Handling Strategy

Throw typed domain exceptions in handlers. A global middleware catches them and maps to RFC 9457 ProblemDetails responses.

### Custom Exception Hierarchy

```csharp
// using System;

public abstract class AppException(string message, int statusCode)
    : Exception(message)
{
    public int StatusCode { get; } = statusCode;
}

public class NotFoundException(string entity, object key)
    : AppException($"{entity} with key '{key}' was not found.", 404);

public class ConflictException(string message)
    : AppException(message, 409);

public class ForbiddenException(string message = "You do not have permission.")
    : AppException(message, 403);

public class BadRequestException(string message)
    : AppException(message, 400);
```

### Global Exception Handling Middleware

```csharp
// using FluentValidation;
// using Microsoft.AspNetCore.Http;
// using Microsoft.AspNetCore.Mvc;
// using Microsoft.Extensions.Logging;

public class ExceptionHandlingMiddleware(
    RequestDelegate next,
    ILogger<ExceptionHandlingMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await next(context);
        }
        catch (ValidationException ex)
        {
            context.Response.StatusCode = 422;
            await context.Response.WriteAsJsonAsync(new ProblemDetails
            {
                Status = 422,
                Title = "Validation Error",
                Detail = "One or more validation errors occurred.",
                Extensions = { ["errors"] = ex.Errors
                    .GroupBy(e => e.PropertyName)
                    .ToDictionary(g => g.Key, g => g.Select(e => e.ErrorMessage).ToArray()) }
            });
        }
        catch (AppException ex)
        {
            logger.LogWarning(ex, "Application exception: {Message}", ex.Message);
            context.Response.StatusCode = ex.StatusCode;
            await context.Response.WriteAsJsonAsync(new ProblemDetails
            {
                Status = ex.StatusCode,
                Title = ex.GetType().Name.Replace("Exception", ""),
                Detail = ex.Message
            });
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Unhandled exception");
            context.Response.StatusCode = 500;
            await context.Response.WriteAsJsonAsync(new ProblemDetails
            {
                Status = 500,
                Title = "Internal Server Error",
                Detail = "An unexpected error occurred."
            });
        }
    }
}

// Registration
app.UseMiddleware<ExceptionHandlingMiddleware>();
```

## Validation Strategy

Use dual validation: **FluentValidation** at the API boundary for input shape, and **domain invariants** inside entity constructors and methods for business rules.

### FluentValidation (Input Shape)

```csharp
// using FluentValidation;

public class CreateOrderCommandValidator : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderCommandValidator()
    {
        RuleFor(x => x.CustomerId).NotEmpty().MaximumLength(50);
        RuleFor(x => x.Items).NotEmpty().WithMessage("Order must have at least one item.");
        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(i => i.ProductId).NotEmpty();
            item.RuleFor(i => i.Quantity).GreaterThan(0);
        });
    }
}
```

FluentValidation runs automatically via the `ValidationBehavior` pipeline behavior shown in Section 8.

### Domain Invariants (Business Rules)

```csharp
public class Order
{
    public int Id { get; private set; }
    public OrderStatus Status { get; private set; }
    private readonly List<OrderItem> _items = [];
    public IReadOnlyList<OrderItem> Items => _items.AsReadOnly();

    public void AddItem(string productId, int quantity, decimal unitPrice)
    {
        if (Status != OrderStatus.Draft)
            throw new ConflictException("Cannot add items to a non-draft order.");

        if (quantity <= 0)
            throw new BadRequestException("Quantity must be positive.");

        _items.Add(new OrderItem(productId, quantity, unitPrice));
    }

    public void Submit()
    {
        if (_items.Count == 0)
            throw new ConflictException("Cannot submit an empty order.");

        Status = OrderStatus.Submitted;
    }
}
```

## DDD Decision Tree

Domain-Driven Design adds overhead. Use it when the domain justifies it.

| Signal | Recommendation |
|--------|---------------|
| Business logic is complex, rules change often, domain experts are available | Full DDD tactical patterns: aggregates, value objects, domain events |
| Mostly CRUD with simple validation | Anemic models are fine -- keep it simple |
| Mix of complex and simple bounded contexts | DDD in complex contexts, simple models in CRUD contexts |

### When DDD Is Worth It

```csharp
// using MediatR;

// Value Object
public record Money(decimal Amount, string Currency)
{
    public static Money operator +(Money a, Money b)
    {
        if (a.Currency != b.Currency)
            throw new InvalidOperationException("Cannot add different currencies.");
        return new Money(a.Amount + b.Amount, a.Currency);
    }
}

// Domain Event
public record OrderSubmittedEvent(int OrderId, string CustomerId, DateTime SubmittedAt)
    : INotification;

// Raising domain events from aggregate
public abstract class AggregateRoot
{
    private readonly List<INotification> _domainEvents = [];
    public IReadOnlyList<INotification> DomainEvents => _domainEvents.AsReadOnly();
    protected void RaiseDomainEvent(INotification domainEvent) => _domainEvents.Add(domainEvent);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

### When DDD Is Not Worth It

For CRUD-heavy contexts, a flat model with FluentValidation is simpler and more maintainable. Do not force aggregates and value objects where there is no complex invariant logic to protect.

## Authentication & Authorization

This skill focuses on the **consumption side** of auth. Assume an external Identity Provider (Keycloak, Auth0, Entra ID) issues JWTs.

### JWT Bearer Setup

```csharp
// using Microsoft.AspNetCore.Authentication.JwtBearer;

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.Authority = builder.Configuration["Auth:Authority"];
        options.Audience = builder.Configuration["Auth:Audience"];
    });
```

### Policy-Based Authorization

```csharp
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("AdminOnly", policy => policy.RequireRole("Admin"))
    .AddPolicy("CanManageOrders", policy =>
        policy.RequireClaim("permission", "orders:manage"));

// Apply to endpoints
app.MapDelete("/api/v1/orders/{id}", async (int id, ISender sender) =>
{
    await sender.Send(new DeleteOrderCommand(id));
    return Results.NoContent();
})
.RequireAuthorization("CanManageOrders");

// Or on controllers
[Authorize(Policy = "AdminOnly")]
[HttpPost("refund")]
public async Task<IActionResult> Refund(RefundCommand command)
    => Ok(await sender.Send(command));
```

## API Versioning

Use Asp.Versioning with URL segment strategy for explicit, discoverable API versions.

```csharp
// using Asp.Versioning;

builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
    options.ApiVersionReader = new UrlSegmentApiVersionReader();
});

// Minimal API versioning
var versionSet = app.NewApiVersionSet()
    .HasApiVersion(new ApiVersion(1, 0))
    .HasApiVersion(new ApiVersion(2, 0))
    .Build();

app.MapGet("/api/v{version:apiVersion}/orders", GetOrdersV1)
    .WithApiVersionSet(versionSet)
    .MapToApiVersion(new ApiVersion(1, 0));

app.MapGet("/api/v{version:apiVersion}/orders", GetOrdersV2)
    .WithApiVersionSet(versionSet)
    .MapToApiVersion(new ApiVersion(2, 0));
```

## Background Processing

Choose based on complexity of your scheduling and retry needs.

| Need | Solution | When |
|------|----------|------|
| Simple in-process queue | `IHostedService` + `Channel<T>` | Fire-and-forget tasks, no persistence needed |
| Persistent jobs, scheduling, retries | Hangfire *or* Quartz.NET | Recurring jobs, must survive app restarts, need dashboards |

### IHostedService + Channels (Simple)

```csharp
// using System.Threading.Channels;
// using Microsoft.Extensions.Hosting;

public class EmailChannel
{
    private readonly Channel<EmailMessage> _channel = Channel.CreateUnbounded<EmailMessage>();
    public ChannelWriter<EmailMessage> Writer => _channel.Writer;
    public ChannelReader<EmailMessage> Reader => _channel.Reader;
}

public class EmailBackgroundService(EmailChannel channel, IEmailSender sender)
    : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        await foreach (var message in channel.Reader.ReadAllAsync(ct))
        {
            await sender.SendAsync(message);
        }
    }
}
```

### Hangfire (Persistent)

```csharp
// using Hangfire;

builder.Services.AddHangfire(config =>
    config.UseSqlServerStorage(connectionString));
builder.Services.AddHangfireServer();

// Enqueue a job
BackgroundJob.Enqueue<IReportGenerator>(x => x.GenerateMonthlyReport());

// Recurring job
RecurringJob.AddOrUpdate<IDataSyncService>(
    "daily-sync",
    x => x.SyncExternalData(),
    Cron.Daily);
```

## Real-time Communication (SignalR)

### Strongly-Typed Hub

```csharp
// using Microsoft.AspNetCore.SignalR;

public interface IOrderNotifications
{
    Task OrderStatusChanged(int orderId, string newStatus);
    Task NewOrderPlaced(int orderId, string customerName);
}

public class OrderHub : Hub<IOrderNotifications>
{
    public async Task JoinOrderGroup(int orderId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"order-{orderId}");
    }

    public async Task LeaveOrderGroup(int orderId)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"order-{orderId}");
    }
}
```

### Sending Notifications from a Handler

```csharp
// using MediatR;
// using Microsoft.AspNetCore.SignalR;

public class OrderSubmittedHandler(IHubContext<OrderHub, IOrderNotifications> hub)
    : INotificationHandler<OrderSubmittedEvent>
{
    public async Task Handle(OrderSubmittedEvent notification, CancellationToken ct)
    {
        await hub.Clients.Group($"order-{notification.OrderId}")
            .OrderStatusChanged(notification.OrderId, "Submitted");
    }
}
```

### SignalR Auth

```csharp
builder.Services.AddSignalR();

app.MapHub<OrderHub>("/hubs/orders")
    .RequireAuthorization();

// Client connects with access token
var connection = new HubConnectionBuilder()
    .WithUrl("https://api.example.com/hubs/orders", options =>
    {
        options.AccessTokenProvider = () => Task.FromResult(token);
    })
    .WithAutomaticReconnect()
    .Build();
```

## Resilience (Polly v8)

Use `Microsoft.Extensions.Http.Resilience` for HTTP client resilience. Polly v8 uses a pipeline-based API.

```csharp
// using Microsoft.Extensions.Http.Resilience;

builder.Services.AddHttpClient<ICatalogClient, CatalogClient>(client =>
{
    client.BaseAddress = new Uri("https://catalog-service/");
})
.AddStandardResilienceHandler(options =>
{
    options.Retry.MaxRetryAttempts = 3;
    options.Retry.Delay = TimeSpan.FromMilliseconds(500);
    options.CircuitBreaker.SamplingDuration = TimeSpan.FromSeconds(10);
    options.AttemptTimeout.Timeout = TimeSpan.FromSeconds(5);
    options.TotalRequestTimeout.Timeout = TimeSpan.FromSeconds(30);
});
```

For custom resilience pipelines beyond HTTP:

```csharp
// using Microsoft.EntityFrameworkCore;
// using Microsoft.Extensions.DependencyInjection;
// using Polly;
// using Polly.Retry;

builder.Services.AddResiliencePipeline("database-retry", pipelineBuilder =>
{
    pipelineBuilder
        .AddRetry(new RetryStrategyOptions
        {
            MaxRetryAttempts = 3,
            Delay = TimeSpan.FromMilliseconds(200),
            BackoffType = DelayBackoffType.Exponential,
            ShouldHandle = new PredicateBuilder().Handle<DbUpdateException>()
        })
        .AddTimeout(TimeSpan.FromSeconds(10));
});
```

## Observability

### Serilog vs Built-in Logging

| Factor | Serilog | Microsoft.Extensions.Logging |
|--------|---------|------------------------------|
| **Structured logging** | First-class, rich enrichers, sinks ecosystem | Supported, fewer built-in enrichers |
| **Sink variety** | 100+ sinks (Seq, Elasticsearch, Datadog, etc.) | Providers via NuGet, fewer choices |
| **Configuration** | File-based config, hot reload | `appsettings.json`, standard |
| **OpenTelemetry** | Full integration via Serilog.Sinks.OpenTelemetry | Native integration |
| **Overhead** | Small additional dependency | Zero additional dependencies |

Both are valid. Use Serilog if you need rich structured logging with specialized sinks. Use built-in logging if you want zero extra dependencies and your observability platform has a native .NET provider.

### OpenTelemetry Setup

```csharp
// using OpenTelemetry.Metrics;
// using OpenTelemetry.Trace;

builder.Services.AddOpenTelemetry()
    .WithTracing(tracing => tracing
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddEntityFrameworkCoreInstrumentation()
        .AddOtlpExporter())
    .WithMetrics(metrics => metrics
        .AddAspNetCoreInstrumentation()
        .AddHttpClientInstrumentation()
        .AddOtlpExporter());
```

## DI Organization (Extension Method Modules)

Group service registrations by feature or layer using `IServiceCollection` extension methods. This keeps `Program.cs` clean and makes each module self-contained.

```csharp
// using FluentValidation;
// using MediatR;
// using Microsoft.EntityFrameworkCore;
// using Microsoft.Extensions.Configuration;
// using Microsoft.Extensions.DependencyInjection;

// In MyApp.Application project
public static class ApplicationServiceRegistration
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(typeof(ApplicationServiceRegistration).Assembly);
            cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
            cfg.AddOpenBehavior(typeof(LoggingBehavior<,>));
        });

        services.AddValidatorsFromAssembly(
            typeof(ApplicationServiceRegistration).Assembly);

        return services;
    }
}

// In MyApp.Infrastructure project
public static class InfrastructureServiceRegistration
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services, IConfiguration config)
    {
        services.AddDbContext<AppDbContext>(options =>
            options.UseSqlServer(config.GetConnectionString("Default")));

        // For Dapper queries, inject AppDbContext and use:
        // var connection = db.Database.GetDbConnection();
        // No separate IDbConnection registration needed

        return services;
    }
}

// Clean Program.cs
builder.Services
    .AddApplication()
    .AddInfrastructure(builder.Configuration);
```

## Configuration (IOptions Pattern)

Use the `IOptions<T>` family for typed configuration. Choose the right interface based on your reload needs:

- **`IOptions<T>`** -- Singleton, read once at startup. Best for settings that never change.
- **`IOptionsSnapshot<T>`** -- Scoped, re-reads per request. Use in request-scoped services when config may change between deployments.
- **`IOptionsMonitor<T>`** -- Singleton with change notifications. Use in singleton services that need to react to config changes without restart.

```csharp
// using Microsoft.Extensions.Options;

builder.Services.Configure<SmtpSettings>(builder.Configuration.GetSection("Smtp"));

// Inject where needed
public class EmailSender(IOptionsMonitor<SmtpSettings> smtpOptions)
{
    public async Task SendAsync(EmailMessage message)
    {
        var settings = smtpOptions.CurrentValue; // always latest
        // ...
    }
}
```

## Testing Strategy

Testing strategy varies by architecture. Match your approach to how the code is structured.

| Architecture | Primary Test Style | Rationale |
|--------------|--------------------|-----------|
| **Clean Architecture** | Unit tests (domain + handlers with mocked deps) | Isolated domain layer, dependency inversion makes mocking natural |
| **Vertical Slice** | Integration tests (`WebApplicationFactory`, real pipeline) | Each slice is end-to-end; testing the pipeline is more valuable than testing parts |
| **Modular Monolith** | Module integration tests + cross-module contract tests | Validate module behavior and that module boundaries hold |

### Integration Test Example (WebApplicationFactory)

```csharp
// using System.Net;
// using System.Net.Http.Json;
// using FluentAssertions;
// using Microsoft.AspNetCore.Mvc;
// using Microsoft.AspNetCore.Mvc.Testing;

public class OrdersApiTests(WebApplicationFactory<Program> factory)
    : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task CreateOrder_ReturnsCreated()
    {
        var client = factory.CreateClient();
        var command = new { CustomerId = "cust-1", Items = new[]
        {
            new { ProductId = "prod-1", Quantity = 2 }
        }};

        var response = await client.PostAsJsonAsync("/api/v1/orders", command);

        response.StatusCode.Should().Be(HttpStatusCode.Created);
    }

    [Fact]
    public async Task GetOrder_NotFound_ReturnsProblemDetails()
    {
        var client = factory.CreateClient();

        var response = await client.GetAsync("/api/v1/orders/99999");

        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Status.Should().Be(404);
    }
}
```

### Unit Test Example (Handler with Mocked DbContext)

```csharp
// using FluentAssertions;
// using Xunit;

[Fact]
public async Task GetOrder_ReturnsDto_WhenOrderExists()
{
    var db = CreateInMemoryDbContext();
    db.Orders.Add(new Order { Id = 1, Status = OrderStatus.Draft });
    await db.SaveChangesAsync();

    var handler = new GetOrderQueryHandler(db);

    var result = await handler.Handle(new GetOrderQuery(1), CancellationToken.None);

    result.Id.Should().Be(1);
}
```

## DB Migrations (EF Core Best Practices)

### Creating and Applying Migrations

```bash
# Create a migration
dotnet ef migrations add AddOrderTable -p MyApp.Infrastructure -s MyApp.Api

# Apply to local database
dotnet ef database update -p MyApp.Infrastructure -s MyApp.Api

# Generate idempotent SQL script for CI/CD
dotnet ef migrations script --idempotent -p MyApp.Infrastructure -s MyApp.Api -o migrate.sql
```

### Migration Bundles for CI/CD

```bash
# Build a self-contained migration executable
dotnet ef migrations bundle -p MyApp.Infrastructure -s MyApp.Api -o efbundle

# Run in production pipeline
./efbundle --connection "Server=prod;Database=MyApp;..."
```

### Best Practices

- **Never call `Database.Migrate()` in production startup** -- use migration bundles or idempotent scripts in your deployment pipeline.
- **Data seeding** -- use `HasData()` in `OnModelCreating` for reference data only. Use migrations for structural seeding.
- **Team conflict handling** -- when two developers create migrations concurrently, delete the conflicting migration, merge code first, then create a new migration from the merged state.
- **Always review generated SQL** -- run `dotnet ef migrations script` and inspect before applying to shared environments.

## Project Structure Templates

### Clean Architecture Layout

```
MyApp/
  MyApp.sln
  src/
    MyApp.Domain/             # Entities, value objects, domain events, interfaces
    MyApp.Application/        # Commands, queries, handlers, DTOs, validators
    MyApp.Infrastructure/     # DbContext, EF configs, external services
    MyApp.Api/                # Program.cs, endpoints/controllers, middleware
  tests/
    MyApp.Domain.Tests/
    MyApp.Application.Tests/
    MyApp.Api.IntegrationTests/
```

### Vertical Slice Layout

```
MyApp/
  MyApp.sln
  src/
    MyApp.Api/
      Features/
        Orders/
          CreateOrder.cs        # Command + Handler + Validator + Endpoint
          GetOrder.cs           # Query + Handler + Endpoint
          OrderDto.cs
        Products/
          GetProducts.cs
          CreateProduct.cs
      Common/
        Behaviors/
        Middleware/
      Data/
        AppDbContext.cs
  tests/
    MyApp.Api.Tests/
```

### Modular Monolith Layout

```
MyApp/
  MyApp.sln
  src/
    MyApp.Host/                 # Composition root, Program.cs
    Modules/
      Orders/
        MyApp.Orders.Api/       # Module endpoints
        MyApp.Orders.Core/      # Commands, queries, domain
        MyApp.Orders.Infra/     # Module-specific data access
        MyApp.Orders.Contracts/ # Public DTOs and integration events
      Catalog/
        MyApp.Catalog.Api/
        MyApp.Catalog.Core/
        MyApp.Catalog.Infra/
        MyApp.Catalog.Contracts/
    MyApp.Shared/               # Cross-cutting: middleware, base classes
  tests/
    Modules/
      MyApp.Orders.Tests/
      MyApp.Catalog.Tests/
    MyApp.Integration.Tests/
```

## References

Detailed guidance for each architecture pattern is available in the companion files:

- **`stacks/clean-architecture.md`** -- Full Clean Architecture template with project references, folder conventions, and sample code
- **`stacks/vertical-slice.md`** -- Vertical Slice template with feature folder conventions and minimal ceremony patterns
- **`stacks/modular-monolith.md`** -- Modular Monolith template with module boundary patterns, integration events, and contract testing

## Reference Guides

Detailed guidance on specific topics:

| Reference | Purpose |
|-----------|---------|
| `references/ddd-patterns.md` | DDD tactical patterns — aggregates, value objects, domain events, strongly-typed IDs |
| `references/testing-strategies.md` | Architecture-specific testing ratios, Testcontainers + Respawn setup, test examples |
| `references/observability.md` | Logging (Serilog vs built-in), OpenTelemetry, correlation IDs, health checks |
| `references/signalr-patterns.md` | Strongly-typed hubs, auth, MediatR integration, Redis backplane, TypeScript client |
| `references/ef-migrations.md` | Migration workflow, bundles, expand-contract pattern, modular monolith schemas |
| `references/error-handling.md` | Exception hierarchy, IExceptionHandler, ProblemDetails, FluentValidation pipeline |

---

**Remember**: There is no single "correct" architecture. Start with the pattern that matches your team's size and domain complexity. Keep things simple early, refactor when complexity demands it, and let the decision trees in this guide help you navigate trade-offs rather than prescribe answers.
