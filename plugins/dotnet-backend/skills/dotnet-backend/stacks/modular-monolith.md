# Modular Monolith Stack

## Overview

The Modular Monolith architecture organizes a single deployable unit into independent modules with explicit boundaries, each owning its own domain, data, and API surface. Modules communicate through integration events and public contracts -- never by reaching into each other's internals. This gives you the boundary discipline of microservices without the distributed-systems tax.

## When to Choose

- Multiple bounded contexts with distinct domain models that should stay isolated
- Team wants service-like boundaries but is not ready for distributed infrastructure (separate databases, message brokers, container orchestration)
- System will likely evolve toward microservices -- modular monolith is the safest on-ramp
- Two to four teams working on the same deployable, needing clear ownership lines
- Complex domain where different modules have different consistency and complexity needs

## When to Avoid

- Simple CRUD application with a single bounded context -- use Vertical Slice instead
- Team of one or two developers on a small API -- Clean Architecture or Vertical Slice is less ceremony
- You already have distributed infrastructure and need independent deployment per service today

## Solution Structure

```
MyApp/
  MyApp.sln
  src/
    Bootstrapper/                          # Host project -- composes all modules
      Bootstrapper.csproj
      Program.cs
      appsettings.json
    Modules/
      Catalog/
        Catalog.Api/                       # Module endpoints (Minimal APIs or Controllers)
          CatalogModule.cs
          Endpoints/
        Catalog.Application/               # Commands, queries, handlers, validators
          Commands/
          Queries/
          Validators/
        Catalog.Domain/                    # Entities, value objects, domain events
          Entities/
          Events/
        Catalog.Infrastructure/            # Module-specific DbContext, EF configs
          Data/
            CatalogDbContext.cs
            Configurations/
          Services/
        Catalog.IntegrationEvents/         # Public contracts other modules may consume
          ProductPriceChangedEvent.cs
      Orders/
        Orders.Api/
          OrdersModule.cs
          Endpoints/
        Orders.Application/
          Commands/
          Queries/
          Validators/
        Orders.Domain/
          Entities/
          Events/
        Orders.Infrastructure/
          Data/
            OrdersDbContext.cs
            Configurations/
          Services/
        Orders.IntegrationEvents/
          OrderSubmittedEvent.cs
    Shared/
      Shared.Abstractions/                 # IModule interface, base types, integration event bus abstraction
        IModule.cs
        IIntegrationEventBus.cs
        IntegrationEvent.cs
      Shared.Infrastructure/               # In-process event bus, shared middleware, common EF interceptors
        InProcessIntegrationEventBus.cs
        Middleware/
  tests/
    Modules/
      Catalog.Tests/                       # Per-module integration tests
      Orders.Tests/
    CrossModule.Tests/                     # Contract tests verifying module boundaries
    SystemIntegration.Tests/               # Full Bootstrapper integration tests
```

## Scaffolding Commands

Run these commands from the solution root to create the full structure.

```bash
# Create solution
dotnet new sln -n MyApp

# -- Shared projects --
dotnet new classlib -n Shared.Abstractions -o src/Shared/Shared.Abstractions
dotnet new classlib -n Shared.Infrastructure -o src/Shared/Shared.Infrastructure
dotnet sln add src/Shared/Shared.Abstractions src/Shared/Shared.Infrastructure
dotnet add src/Shared/Shared.Infrastructure reference src/Shared/Shared.Abstractions

# -- Catalog module --
dotnet new classlib -n Catalog.Domain -o src/Modules/Catalog/Catalog.Domain
dotnet new classlib -n Catalog.Application -o src/Modules/Catalog/Catalog.Application
dotnet new classlib -n Catalog.Infrastructure -o src/Modules/Catalog/Catalog.Infrastructure
dotnet new classlib -n Catalog.IntegrationEvents -o src/Modules/Catalog/Catalog.IntegrationEvents
dotnet new classlib -n Catalog.Api -o src/Modules/Catalog/Catalog.Api
dotnet sln add \
  src/Modules/Catalog/Catalog.Domain \
  src/Modules/Catalog/Catalog.Application \
  src/Modules/Catalog/Catalog.Infrastructure \
  src/Modules/Catalog/Catalog.IntegrationEvents \
  src/Modules/Catalog/Catalog.Api

# Catalog project references (dependency direction: Api -> Application -> Domain, Infrastructure -> Application)
dotnet add src/Modules/Catalog/Catalog.Application reference src/Modules/Catalog/Catalog.Domain
dotnet add src/Modules/Catalog/Catalog.Infrastructure reference src/Modules/Catalog/Catalog.Application
dotnet add src/Modules/Catalog/Catalog.Infrastructure reference src/Shared/Shared.Infrastructure
dotnet add src/Modules/Catalog/Catalog.Api reference src/Modules/Catalog/Catalog.Application
dotnet add src/Modules/Catalog/Catalog.Api reference src/Modules/Catalog/Catalog.Infrastructure
dotnet add src/Modules/Catalog/Catalog.Api reference src/Shared/Shared.Abstractions
dotnet add src/Modules/Catalog/Catalog.IntegrationEvents reference src/Shared/Shared.Abstractions

# -- Orders module (same pattern) --
dotnet new classlib -n Orders.Domain -o src/Modules/Orders/Orders.Domain
dotnet new classlib -n Orders.Application -o src/Modules/Orders/Orders.Application
dotnet new classlib -n Orders.Infrastructure -o src/Modules/Orders/Orders.Infrastructure
dotnet new classlib -n Orders.IntegrationEvents -o src/Modules/Orders/Orders.IntegrationEvents
dotnet new classlib -n Orders.Api -o src/Modules/Orders/Orders.Api
dotnet sln add \
  src/Modules/Orders/Orders.Domain \
  src/Modules/Orders/Orders.Application \
  src/Modules/Orders/Orders.Infrastructure \
  src/Modules/Orders/Orders.IntegrationEvents \
  src/Modules/Orders/Orders.Api

dotnet add src/Modules/Orders/Orders.Application reference src/Modules/Orders/Orders.Domain
dotnet add src/Modules/Orders/Orders.Infrastructure reference src/Modules/Orders/Orders.Application
dotnet add src/Modules/Orders/Orders.Infrastructure reference src/Shared/Shared.Infrastructure
dotnet add src/Modules/Orders/Orders.Api reference src/Modules/Orders/Orders.Application
dotnet add src/Modules/Orders/Orders.Api reference src/Modules/Orders/Orders.Infrastructure
dotnet add src/Modules/Orders/Orders.Api reference src/Shared/Shared.Abstractions

# Cross-module reference: Orders consumes Catalog's integration events (NOT Catalog internals)
dotnet add src/Modules/Orders/Orders.Application reference src/Modules/Catalog/Catalog.IntegrationEvents
dotnet add src/Modules/Orders/Orders.IntegrationEvents reference src/Shared/Shared.Abstractions

# -- Bootstrapper (host) --
dotnet new webapi -n Bootstrapper -o src/Bootstrapper --use-minimal-apis
dotnet sln add src/Bootstrapper
dotnet add src/Bootstrapper reference src/Modules/Catalog/Catalog.Api
dotnet add src/Bootstrapper reference src/Modules/Orders/Orders.Api
dotnet add src/Bootstrapper reference src/Shared/Shared.Infrastructure

# -- Test projects --
dotnet new xunit -n Catalog.Tests -o tests/Modules/Catalog.Tests
dotnet new xunit -n Orders.Tests -o tests/Modules/Orders.Tests
dotnet new xunit -n CrossModule.Tests -o tests/CrossModule.Tests
dotnet new xunit -n SystemIntegration.Tests -o tests/SystemIntegration.Tests
dotnet sln add \
  tests/Modules/Catalog.Tests \
  tests/Modules/Orders.Tests \
  tests/CrossModule.Tests \
  tests/SystemIntegration.Tests

# Test project references
dotnet add tests/Modules/Catalog.Tests reference src/Modules/Catalog/Catalog.Api
dotnet add tests/Modules/Catalog.Tests reference src/Bootstrapper
dotnet add tests/Modules/Orders.Tests reference src/Modules/Orders/Orders.Api
dotnet add tests/Modules/Orders.Tests reference src/Bootstrapper
dotnet add tests/CrossModule.Tests reference src/Bootstrapper
dotnet add tests/SystemIntegration.Tests reference src/Bootstrapper

# -- NuGet packages --
dotnet add src/Shared/Shared.Abstractions package MediatR.Contracts
dotnet add src/Shared/Shared.Infrastructure package MediatR
dotnet add src/Shared/Shared.Infrastructure package Microsoft.Extensions.DependencyInjection.Abstractions

# Per-module packages (repeat for each module's Application and Infrastructure)
dotnet add src/Modules/Catalog/Catalog.Application package MediatR
dotnet add src/Modules/Catalog/Catalog.Application package FluentValidation.DependencyInjectionExtensions
dotnet add src/Modules/Catalog/Catalog.Infrastructure package Microsoft.EntityFrameworkCore.SqlServer
dotnet add src/Modules/Catalog/Catalog.Infrastructure package Dapper

dotnet add src/Modules/Orders/Orders.Application package MediatR
dotnet add src/Modules/Orders/Orders.Application package FluentValidation.DependencyInjectionExtensions
dotnet add src/Modules/Orders/Orders.Infrastructure package Microsoft.EntityFrameworkCore.SqlServer
dotnet add src/Modules/Orders/Orders.Infrastructure package Dapper

# Bootstrapper packages
dotnet add src/Bootstrapper package Serilog.AspNetCore
dotnet add src/Bootstrapper package Microsoft.EntityFrameworkCore.Design

# Test packages
dotnet add tests/Modules/Catalog.Tests package Microsoft.AspNetCore.Mvc.Testing
dotnet add tests/Modules/Catalog.Tests package FluentAssertions
dotnet add tests/Modules/Catalog.Tests package Testcontainers.MsSql
dotnet add tests/Modules/Orders.Tests package Microsoft.AspNetCore.Mvc.Testing
dotnet add tests/Modules/Orders.Tests package FluentAssertions
dotnet add tests/Modules/Orders.Tests package Testcontainers.MsSql
dotnet add tests/CrossModule.Tests package Microsoft.AspNetCore.Mvc.Testing
dotnet add tests/CrossModule.Tests package FluentAssertions
dotnet add tests/SystemIntegration.Tests package Microsoft.AspNetCore.Mvc.Testing
dotnet add tests/SystemIntegration.Tests package FluentAssertions
dotnet add tests/SystemIntegration.Tests package Testcontainers.MsSql
```

## Module Registration Pattern

### IModule Interface

Define a standard contract every module implements. This keeps the Bootstrapper decoupled from module internals.

```csharp
// Shared.Abstractions/IModule.cs
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Shared.Abstractions;

public interface IModule
{
    string Name { get; }
    void RegisterServices(IServiceCollection services, IConfiguration configuration);
    void MapEndpoints(IEndpointRouteBuilder endpoints);
}
```

### Module Implementation

Each module exposes a single class implementing `IModule`. This is the only public entry point the Bootstrapper knows about.

```csharp
// Catalog.Api/CatalogModule.cs
using Catalog.Application.Commands;
using Catalog.Api.Endpoints;
using Catalog.Infrastructure.Data;
using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Shared.Abstractions;

namespace Catalog.Api;

public class CatalogModule : IModule
{
    public string Name => "Catalog";

    public void RegisterServices(IServiceCollection services, IConfiguration configuration)
    {
        // MediatR scoped to this module's assembly
        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(typeof(CatalogModule).Assembly);
            cfg.RegisterServicesFromAssembly(typeof(CreateProductCommand).Assembly);
            cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
        });

        services.AddValidatorsFromAssembly(typeof(CreateProductCommand).Assembly);

        // Module-specific DbContext with schema isolation
        services.AddDbContext<CatalogDbContext>(options =>
            options.UseSqlServer(
                configuration.GetConnectionString("Default"),
                sql => sql.MigrationsHistoryTable("__EFMigrationsHistory", "catalog")));

        // For Dapper queries, inject the module's DbContext and use:
        // var connection = db.Database.GetDbConnection();
    }

    public void MapEndpoints(IEndpointRouteBuilder endpoints)
    {
        var group = endpoints.MapGroup("/api/v1/catalog")
            .WithTags("Catalog")
            .WithOpenApi();

        group.MapGet("/products", GetProducts.Handle);
        group.MapGet("/products/{id:int}", GetProductById.Handle);
        group.MapPost("/products", CreateProduct.Handle);
        group.MapPut("/products/{id:int}", UpdateProduct.Handle);
    }
}
```

### Bootstrapper Program.cs

The host discovers and composes all modules. No module-specific logic leaks into Program.cs.

```csharp
// Bootstrapper/Program.cs
using Catalog.Api;
using Orders.Api;
using Shared.Abstractions;
using Shared.Infrastructure;

var builder = WebApplication.CreateBuilder(args);

// Discover all modules
var modules = DiscoverModules();

// Register shared infrastructure
builder.Services.AddSharedInfrastructure(builder.Configuration);

// Register each module's services
foreach (var module in modules)
{
    module.RegisterServices(builder.Services, builder.Configuration);
}

// Shared services
builder.Services.AddProblemDetails();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();

app.UseExceptionHandler();
app.UseSwagger();
app.UseSwaggerUI();
app.UseAuthentication();
app.UseAuthorization();

// Map each module's endpoints
foreach (var module in modules)
{
    module.MapEndpoints(app);
}

app.Run();

// Module discovery -- explicit assembly list for predictable startup
static IModule[] DiscoverModules()
{
    var moduleTypes = new[]
    {
        typeof(Catalog.Api.CatalogModule),
        typeof(Orders.Api.OrdersModule)
    };

    return moduleTypes
        .Select(Activator.CreateInstance)
        .OfType<IModule>()
        .ToArray();
}

// Make Program accessible for WebApplicationFactory in tests
public partial class Program;
```

## Module Communication

Modules never reference each other's internal projects (Domain, Application, Infrastructure). Communication happens exclusively through integration events and public contracts.

### Integration Event Abstractions

```csharp
// Shared.Abstractions/IntegrationEvent.cs
using MediatR;

namespace Shared.Abstractions;

public abstract record IntegrationEvent
{
    public Guid EventId { get; init; } = Guid.NewGuid();
    public DateTime OccurredAt { get; init; } = DateTime.UtcNow;
}

// Shared.Abstractions/IIntegrationEventBus.cs
namespace Shared.Abstractions;

public interface IIntegrationEventBus
{
    Task PublishAsync<T>(T integrationEvent, CancellationToken ct = default) where T : IntegrationEvent;
}

// Shared.Abstractions/IIntegrationEventHandler.cs
namespace Shared.Abstractions;

public interface IIntegrationEventHandler<in TEvent> where TEvent : IntegrationEvent
{
    Task HandleAsync(TEvent @event, CancellationToken ct = default);
}
```

### In-Process Event Bus (MediatR-Backed)

For a monolith, an in-process bus is sufficient. When you extract a module to a service, swap this for RabbitMQ, Kafka, or Azure Service Bus without changing publisher or handler code.

```csharp
// Shared.Infrastructure/InProcessIntegrationEventBus.cs
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Shared.Abstractions;

namespace Shared.Infrastructure;

public class InProcessIntegrationEventBus(IServiceProvider serviceProvider, ILogger<InProcessIntegrationEventBus> logger)
    : IIntegrationEventBus
{
    public async Task PublishAsync<T>(T integrationEvent, CancellationToken ct = default)
        where T : IntegrationEvent
    {
        var eventType = integrationEvent.GetType();
        logger.LogInformation("Publishing integration event {EventType} ({EventId})",
            eventType.Name, integrationEvent.EventId);

        using var scope = serviceProvider.CreateScope();
        var handlerType = typeof(IIntegrationEventHandler<>).MakeGenericType(eventType);
        var handlers = scope.ServiceProvider.GetServices(handlerType);

        var exceptions = new List<Exception>();

        foreach (var handler in handlers)
        {
            try
            {
                var method = handlerType.GetMethod(nameof(IIntegrationEventHandler<IntegrationEvent>.HandleAsync))!;
                await (Task)method.Invoke(handler, [integrationEvent, ct])!;
            }
            catch (Exception ex)
            {
                exceptions.Add(ex);
                logger.LogError(ex, "Handler {HandlerType} failed for {EventType}",
                    handler!.GetType().Name, eventType.Name);
            }
        }

        if (exceptions.Count > 0)
            throw new AggregateException("Integration event handler(s) failed", exceptions);
    }
}

// Shared.Infrastructure/SharedInfrastructureRegistration.cs
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Shared.Abstractions;

namespace Shared.Infrastructure;

public static class SharedInfrastructureRegistration
{
    public static IServiceCollection AddSharedInfrastructure(
        this IServiceCollection services, IConfiguration configuration)
    {
        services.AddSingleton<IIntegrationEventBus, InProcessIntegrationEventBus>();
        return services;
    }
}
```

### Defining Integration Events (Module Public Contract)

Each module's `IntegrationEvents` project contains only the public contracts other modules may consume. These are the only types that cross module boundaries.

```csharp
// Catalog.IntegrationEvents/ProductPriceChangedEvent.cs
using Shared.Abstractions;

namespace Catalog.IntegrationEvents;

public record ProductPriceChangedEvent(
    int ProductId,
    string ProductName,
    decimal OldPrice,
    decimal NewPrice) : IntegrationEvent;

// Catalog.IntegrationEvents/ProductCreatedEvent.cs
namespace Catalog.IntegrationEvents;

public record ProductCreatedEvent(
    int ProductId,
    string Name,
    string Sku,
    decimal Price) : IntegrationEvent;
```

### Publishing Integration Events

Publish after the domain operation succeeds and the DbContext has saved.

```csharp
// Catalog.Application/Commands/UpdateProductPriceHandler.cs
using Catalog.Domain.Entities;
using Catalog.Infrastructure.Data;
using Catalog.IntegrationEvents;
using MediatR;
using Shared.Abstractions;

namespace Catalog.Application.Commands;

public class UpdateProductPriceHandler(
    CatalogDbContext db,
    IIntegrationEventBus eventBus)
    : IRequestHandler<UpdateProductPriceCommand>
{
    public async Task Handle(UpdateProductPriceCommand request, CancellationToken ct)
    {
        var product = await db.Products.FindAsync([request.ProductId], ct)
            ?? throw new NotFoundException(nameof(Product), request.ProductId);

        var oldPrice = product.Price;
        product.UpdatePrice(request.NewPrice); // domain method with invariant checks

        await db.SaveChangesAsync(ct);

        // Publish integration event AFTER successful save
        await eventBus.PublishAsync(new ProductPriceChangedEvent(
            product.Id, product.Name, oldPrice, request.NewPrice), ct);
    }
}
```

### Consuming Integration Events in Another Module

The Orders module reacts to Catalog events without referencing Catalog internals.

```csharp
// Orders.Application/IntegrationEventHandlers/ProductPriceChangedHandler.cs
using Catalog.IntegrationEvents;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using Orders.Domain.Entities;
using Orders.Infrastructure.Data;
using Shared.Abstractions;

namespace Orders.Application.IntegrationEventHandlers;

// IMPORTANT: Integration event handlers should be idempotent.
// Consider tracking processed EventIds to handle redelivery.
public class ProductPriceChangedHandler(
    OrdersDbContext db,
    ILogger<ProductPriceChangedHandler> logger)
    : IIntegrationEventHandler<ProductPriceChangedEvent>
{
    public async Task HandleAsync(ProductPriceChangedEvent @event, CancellationToken ct)
    {
        logger.LogInformation(
            "Product {ProductId} price changed from {OldPrice} to {NewPrice}",
            @event.ProductId, @event.OldPrice, @event.NewPrice);

        // Update cached product price in draft orders
        var draftItems = await db.OrderItems
            .Include(i => i.Order)
            .Where(i => i.ProductId == @event.ProductId && i.Order.Status == OrderStatus.Draft)
            .ToListAsync(ct);

        foreach (var item in draftItems)
        {
            item.UpdateUnitPrice(@event.NewPrice);
        }

        await db.SaveChangesAsync(ct);
    }
}
```

### Registering Integration Event Handlers

Each module registers its own handlers during DI setup.

```csharp
// In OrdersModule.RegisterServices
using Catalog.IntegrationEvents;
using Orders.Application.IntegrationEventHandlers;
using Shared.Abstractions;

services.AddScoped<IIntegrationEventHandler<ProductPriceChangedEvent>, ProductPriceChangedHandler>();
```

## Per-Module DbContext with Schema Separation

Each module owns its own DbContext targeting a separate database schema. All modules share the same physical database but are logically isolated.

```csharp
// Catalog.Infrastructure/Data/CatalogDbContext.cs
using Catalog.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace Catalog.Infrastructure.Data;

public class CatalogDbContext(DbContextOptions<CatalogDbContext> options) : DbContext(options)
{
    public DbSet<Product> Products => Set<Product>();
    public DbSet<Category> Categories => Set<Category>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // All Catalog tables live in the "catalog" schema
        modelBuilder.HasDefaultSchema("catalog");
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(CatalogDbContext).Assembly);
    }
}

// Orders.Infrastructure/Data/OrdersDbContext.cs
using Microsoft.EntityFrameworkCore;
using Orders.Domain.Entities;

namespace Orders.Infrastructure.Data;

public class OrdersDbContext(DbContextOptions<OrdersDbContext> options) : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // All Orders tables live in the "orders" schema
        modelBuilder.HasDefaultSchema("orders");
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(OrdersDbContext).Assembly);
    }
}
```

### EF Configuration Example

```csharp
// Catalog.Infrastructure/Data/Configurations/ProductConfiguration.cs
using Catalog.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

namespace Catalog.Infrastructure.Data.Configurations;

public class ProductConfiguration : IEntityTypeConfiguration<Product>
{
    public void Configure(EntityTypeBuilder<Product> builder)
    {
        builder.ToTable("Products"); // resolves to catalog.Products
        builder.HasKey(p => p.Id);
        builder.Property(p => p.Name).HasMaxLength(200).IsRequired();
        builder.Property(p => p.Sku).HasMaxLength(50).IsRequired();
        builder.HasIndex(p => p.Sku).IsUnique();
        builder.Property(p => p.Price).HasPrecision(18, 2);
    }
}
```

### Migrations Per Module

Each module manages its own migrations independently.

```bash
# Catalog migrations
dotnet ef migrations add InitialCatalog \
  -p src/Modules/Catalog/Catalog.Infrastructure \
  -s src/Bootstrapper \
  --context CatalogDbContext

# Orders migrations
dotnet ef migrations add InitialOrders \
  -p src/Modules/Orders/Orders.Infrastructure \
  -s src/Bootstrapper \
  --context OrdersDbContext

# Apply all
dotnet ef database update -p src/Modules/Catalog/Catalog.Infrastructure -s src/Bootstrapper --context CatalogDbContext
dotnet ef database update -p src/Modules/Orders/Orders.Infrastructure -s src/Bootstrapper --context OrdersDbContext
```

## Module Endpoint Examples

### Minimal API Endpoints

```csharp
// Catalog.Api/Endpoints/CreateProduct.cs
using Catalog.Application.Commands;
using MediatR;
using Microsoft.AspNetCore.Http;

namespace Catalog.Api.Endpoints;

public static class CreateProduct
{
    public static async Task<IResult> Handle(
        CreateProductCommand command,
        ISender sender,
        CancellationToken ct)
    {
        var productId = await sender.Send(command, ct);
        return Results.Created($"/api/v1/catalog/products/{productId}", new { id = productId });
    }
}

// Catalog.Api/Endpoints/GetProducts.cs
using Catalog.Application.Queries;
using MediatR;
using Microsoft.AspNetCore.Http;

namespace Catalog.Api.Endpoints;

public static class GetProducts
{
    public static async Task<IResult> Handle(
        [AsParameters] GetProductsQuery query,
        ISender sender,
        CancellationToken ct)
    {
        var result = await sender.Send(query, ct);
        return Results.Ok(result);
    }
}
```

### Controller-Based Alternative

Modules can mix API styles. Use Controllers when model binding complexity justifies the structure.

```csharp
// Orders.Api/Controllers/OrdersController.cs
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Orders.Application.Commands;
using Orders.Application.Queries;

namespace Orders.Api.Controllers;

[ApiController]
[Route("api/v1/orders")]
public class OrdersController(ISender sender) : ControllerBase
{
    [HttpPost]
    [ProducesResponseType(typeof(int), StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ProblemDetails), StatusCodes.Status422UnprocessableEntity)]
    public async Task<IActionResult> Create(CreateOrderCommand command, CancellationToken ct)
    {
        var orderId = await sender.Send(command, ct);
        return CreatedAtAction(nameof(GetById), new { id = orderId }, new { id = orderId });
    }

    [HttpGet("{id:int}")]
    public async Task<IActionResult> GetById(int id, CancellationToken ct)
    {
        var order = await sender.Send(new GetOrderQuery(id), ct);
        return Ok(order);
    }

    [HttpPost("{id:int}/submit")]
    public async Task<IActionResult> Submit(int id, CancellationToken ct)
    {
        await sender.Send(new SubmitOrderCommand(id), ct);
        return NoContent();
    }
}
```

When using Controllers, add `services.AddControllers()` and `app.MapControllers()` in the module registration or Bootstrapper.

## Testing Strategy

### Per-Module Integration Tests

Test each module in isolation using `WebApplicationFactory` with a real database (Testcontainers). This validates the full pipeline: endpoint, MediatR, handler, validation, DbContext.

```csharp
// tests/Modules/Catalog.Tests/CatalogModuleFixture.cs
using Catalog.Infrastructure.Data;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Shared.Abstractions;
using Testcontainers.MsSql;
using Xunit;

namespace Catalog.Tests;

public class CatalogModuleFixture : IAsyncLifetime
{
    private readonly MsSqlContainer _sqlContainer = new MsSqlBuilder()
        .WithImage("mcr.microsoft.com/mssql/server:2022-latest")
        .Build();

    public string ConnectionString => _sqlContainer.GetConnectionString();

    public async Task InitializeAsync()
    {
        await _sqlContainer.StartAsync();
    }

    public async Task DisposeAsync()
    {
        await _sqlContainer.DisposeAsync();
    }
}

public class CatalogApiFactory(CatalogModuleFixture fixture)
    : WebApplicationFactory<Program>
{
    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Replace connection string with Testcontainers instance
            services.RemoveAll<DbContextOptions<CatalogDbContext>>();
            services.AddDbContext<CatalogDbContext>(options =>
                options.UseSqlServer(fixture.ConnectionString,
                    sql => sql.MigrationsHistoryTable("__EFMigrationsHistory", "catalog")));
        });

        builder.ConfigureTestServices(services =>
        {
            // Replace integration event bus with a test spy
            services.AddSingleton<IIntegrationEventBus, TestIntegrationEventBus>();
        });
    }
}

// tests/Modules/Catalog.Tests/ProductEndpointTests.cs
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using FluentAssertions;
using Microsoft.AspNetCore.Mvc;
using Xunit;

namespace Catalog.Tests;

public class ProductEndpointTests : IClassFixture<CatalogModuleFixture>
{
    private readonly HttpClient _client;

    public ProductEndpointTests(CatalogModuleFixture fixture)
    {
        var factory = new CatalogApiFactory(fixture);
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task CreateProduct_ValidInput_ReturnsCreated()
    {
        var command = new
        {
            Name = "Widget",
            Sku = "WDG-001",
            Price = 29.99m,
            CategoryId = 1
        };

        var response = await _client.PostAsJsonAsync("/api/v1/catalog/products", command);

        response.StatusCode.Should().Be(HttpStatusCode.Created);
        var body = await response.Content.ReadFromJsonAsync<JsonElement>();
        body.GetProperty("id").GetInt32().Should().BeGreaterThan(0);
    }

    [Fact]
    public async Task CreateProduct_MissingSku_ReturnsProblemDetails()
    {
        var command = new { Name = "Widget", Sku = "", Price = 29.99m };

        var response = await _client.PostAsJsonAsync("/api/v1/catalog/products", command);

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
        var problem = await response.Content.ReadFromJsonAsync<ProblemDetails>();
        problem!.Title.Should().Be("Validation Error");
    }
}
```

### Test Spy for Integration Events

Capture published events in tests to verify module behavior without side effects.

```csharp
// tests/Modules/Catalog.Tests/TestIntegrationEventBus.cs
using Shared.Abstractions;

namespace Catalog.Tests;

public class TestIntegrationEventBus : IIntegrationEventBus
{
    private readonly List<IntegrationEvent> _publishedEvents = [];

    public IReadOnlyList<IntegrationEvent> PublishedEvents => _publishedEvents.AsReadOnly();

    public Task PublishAsync<T>(T integrationEvent, CancellationToken ct = default)
        where T : IntegrationEvent
    {
        _publishedEvents.Add(integrationEvent);
        return Task.CompletedTask;
    }

    public T? GetPublished<T>() where T : IntegrationEvent
        => _publishedEvents.OfType<T>().FirstOrDefault();

    public void Clear() => _publishedEvents.Clear();
}
```

### Cross-Module Contract Tests

Verify that module boundaries hold: module A publishes events that module B can deserialize and handle without runtime errors.

```csharp
// tests/CrossModule.Tests/CatalogOrdersContractTests.cs
using System.Text.Json;
using Catalog.IntegrationEvents;
using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Shared.Abstractions;
using Xunit;

namespace CrossModule.Tests;

public class CatalogOrdersContractTests
{
    [Fact]
    public void ProductPriceChangedEvent_CanBeDeserialized_ByOrdersHandler()
    {
        // Catalog publishes this event
        var @event = new ProductPriceChangedEvent(
            ProductId: 1,
            ProductName: "Widget",
            OldPrice: 19.99m,
            NewPrice: 24.99m);

        // Serialize as if crossing a boundary
        var json = JsonSerializer.Serialize(@event);
        var deserialized = JsonSerializer.Deserialize<ProductPriceChangedEvent>(json);

        // Orders module can consume it
        deserialized.Should().NotBeNull();
        deserialized!.ProductId.Should().Be(1);
        deserialized.NewPrice.Should().Be(24.99m);
        deserialized.EventId.Should().NotBeEmpty();
        deserialized.OccurredAt.Should().BeCloseTo(DateTime.UtcNow, TimeSpan.FromSeconds(5));
    }

    [Fact]
    public async Task OrdersModule_HandlesProductPriceChanged_WithoutErrors()
    {
        // Arrange -- set up Orders module with test database
        await using var factory = new WebApplicationFactory<Program>();
        using var scope = factory.Services.CreateScope();
        var handler = scope.ServiceProvider.GetRequiredService<IIntegrationEventHandler<ProductPriceChangedEvent>>();

        var @event = new ProductPriceChangedEvent(1, "Widget", 19.99m, 24.99m);

        // Act and Assert -- handler does not throw
        await handler.Invoking(h => h.HandleAsync(@event))
            .Should().NotThrowAsync();
    }
}
```

### Full System Integration Tests

Test multi-module workflows end-to-end through the Bootstrapper.

```csharp
// tests/SystemIntegration.Tests/OrderWorkflowTests.cs
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Xunit;

namespace SystemIntegration.Tests;

public class OrderWorkflowTests(WebApplicationFactory<Program> factory)
    : IClassFixture<WebApplicationFactory<Program>>
{
    [Fact]
    public async Task FullOrderWorkflow_CreateProduct_ThenOrder_ThenSubmit()
    {
        var client = factory.CreateClient();

        // Step 1: Create a product in Catalog module
        var productResponse = await client.PostAsJsonAsync("/api/v1/catalog/products", new
        {
            Name = "Test Product",
            Sku = "TST-001",
            Price = 49.99m
        });
        productResponse.StatusCode.Should().Be(HttpStatusCode.Created);

        // Step 2: Create an order in Orders module
        var orderResponse = await client.PostAsJsonAsync("/api/v1/orders", new
        {
            CustomerId = "cust-1",
            Items = new[] { new { ProductId = 1, Quantity = 2 } }
        });
        orderResponse.StatusCode.Should().Be(HttpStatusCode.Created);

        // Step 3: Submit the order
        var submitResponse = await client.PostAsync("/api/v1/orders/1/submit", null);
        submitResponse.StatusCode.Should().Be(HttpStatusCode.NoContent);

        // Step 4: Verify order status
        var getResponse = await client.GetFromJsonAsync<JsonElement>("/api/v1/orders/1");
        getResponse.GetProperty("status").GetString().Should().Be("Submitted");
    }
}
```

## Boundary Enforcement Rules

These rules prevent modules from degrading into a distributed monolith or a tightly coupled mess.

1. **No cross-module DbContext access.** Module A never injects or queries Module B's DbContext. Data flows through integration events or public API calls.

2. **IntegrationEvents project is the public contract.** Only reference another module's `IntegrationEvents` project, never its `Application`, `Domain`, or `Infrastructure`.

3. **No shared entity types.** If both modules need a `Product` concept, each defines its own representation. The Catalog module owns the source of truth; Orders keeps a local projection updated via events.

4. **Integration events are immutable records.** Once published, their shape is a contract. Use additive changes (new optional properties) for evolution; never remove or rename fields.

5. **Each module has its own MediatR registration.** Handlers from Module A should not accidentally process commands from Module B.

## Migration Path to Microservices

The modular monolith is designed so each module can be extracted into an independent service with minimal code changes.

### What Changes When Extracting a Module

| Concern | Monolith (Current) | Microservice (Future) |
|---------|--------------------|-----------------------|
| **Deployment** | Single process | Separate container/process per service |
| **Database** | Shared database, separate schemas | Separate databases |
| **Event bus** | `InProcessIntegrationEventBus` | RabbitMQ, Kafka, or Azure Service Bus adapter |
| **Service calls** | In-process method calls via MediatR | HTTP/gRPC client calls |
| **Configuration** | Single `appsettings.json` | Per-service config, service discovery |
| **Auth** | Shared middleware | Per-service JWT validation or API gateway |

### Extraction Steps

1. **Provision a separate database** for the module. Run its EF migrations against the new database.
2. **Swap the event bus implementation** from `InProcessIntegrationEventBus` to a message broker adapter (same `IIntegrationEventBus` interface).
3. **Create a standalone ASP.NET host** for the module. Copy the module's `RegisterServices` and `MapEndpoints` into the new `Program.cs`.
4. **Replace in-process module API calls** with HTTP/gRPC clients using the existing contract types from the `IntegrationEvents` project.
5. **Update the Bootstrapper** to remove the extracted module and route its traffic to the new service (via API gateway or reverse proxy).
6. **Deploy and verify.** Run cross-module contract tests against the new service boundary.

### Why This Works

The key investment is the `IntegrationEvents` project and the `IIntegrationEventBus` abstraction. Because modules already communicate through serializable events and never share internal state, extraction is a deployment change rather than an architectural rewrite. The contract tests you wrote during monolith development continue to validate the boundary after extraction.

## Key NuGet Packages Summary

| Package | Where | Purpose |
|---------|-------|---------|
| `MediatR` | Per-module Application | CQRS, pipeline behaviors |
| `MediatR.Contracts` | Shared.Abstractions | `IRequest`, `INotification` interfaces only |
| `FluentValidation.DependencyInjectionExtensions` | Per-module Application | Input validation |
| `Microsoft.EntityFrameworkCore.SqlServer` | Per-module Infrastructure | Data access |
| `Dapper` | Per-module Infrastructure | Performance-critical queries |
| `Serilog.AspNetCore` | Bootstrapper | Structured logging |
| `Asp.Versioning.Http` | Bootstrapper or per-module Api | API versioning |
| `Microsoft.AspNetCore.Mvc.Testing` | Test projects | `WebApplicationFactory` |
| `Testcontainers.MsSql` | Test projects | Real database in tests |
| `FluentAssertions` | Test projects | Readable test assertions |
