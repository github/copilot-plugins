# Vertical Slice Architecture Stack

## Overview

Vertical Slice Architecture organizes code by feature instead of technical layer. Each slice owns its endpoint, request/response models, validation, handler logic, and tests in a single cohesive unit. This eliminates cross-layer abstractions like repositories and services, keeping each feature self-contained and independently deployable.

## When to Use

- Rapid feature delivery where each slice ships independently
- Small-to-medium teams (2-8 developers) working on distinct features
- CRUD-heavy APIs with clear per-feature boundaries
- Projects that benefit from low coupling between features
- Greenfield services or microservices with focused domains

## When to Avoid

- Complex cross-feature domain logic requiring rich domain models and shared aggregates
- Systems where business rules span many features and need a unified domain layer
- Very large teams that need strict architectural layering for governance

## Solution Structure

```
src/
  MyApp/
    Features/
      Products/
        CreateProduct.cs          # Endpoint + Command + Handler + Validator
        GetProduct.cs             # Endpoint + Query + Handler
        ListProducts.cs           # Endpoint + Query + Handler
        UpdateProduct.cs
        DeleteProduct.cs
        ProductDto.cs             # Shared DTOs within the feature
      Orders/
        CreateOrder.cs
        GetOrder.cs
        ListOrders.cs
        OrderDto.cs
    Common/
      Behaviors/
        ValidationBehavior.cs     # MediatR pipeline behavior
        LoggingBehavior.cs
      Middleware/
        ExceptionHandlingMiddleware.cs
      Exceptions/
        AppException.cs
        NotFoundException.cs
        ValidationException.cs
        ConflictException.cs
      Extensions/
        ServiceCollectionExtensions.cs
        WebApplicationExtensions.cs
    Data/
      AppDbContext.cs
      Configurations/
        ProductConfiguration.cs
        OrderConfiguration.cs
    Domain/
      Product.cs                  # Entity with domain invariants
      Order.cs
      OrderItem.cs
    Program.cs
    appsettings.json
tests/
  MyApp.Tests/
    Features/
      Products/
        CreateProductTests.cs
        GetProductTests.cs
        ListProductsTests.cs
    Common/
      TestWebApplicationFactory.cs
      TestDatabaseFixture.cs
```

## Scaffolding Commands

```bash
# Install EF Core tools (required for migrations)
dotnet tool install --global dotnet-ef

# Create solution
dotnet new sln -n MyApp

# Create web API project (Minimal API template)
dotnet new webapi -n MyApp -o src/MyApp --use-minimal-apis

# Create test project
dotnet new xunit -n MyApp.Tests -o tests/MyApp.Tests

# Add projects to solution
dotnet sln add src/MyApp/MyApp.csproj
dotnet sln add tests/MyApp.Tests/MyApp.Tests.csproj

# Add test project reference
dotnet add tests/MyApp.Tests reference src/MyApp

# Create feature directories
mkdir -p src/MyApp/Features/Products
mkdir -p src/MyApp/Features/Orders
mkdir -p src/MyApp/Common/Behaviors
mkdir -p src/MyApp/Common/Middleware
mkdir -p src/MyApp/Common/Exceptions
mkdir -p src/MyApp/Common/Extensions
mkdir -p src/MyApp/Data/Configurations
mkdir -p src/MyApp/Domain
mkdir -p tests/MyApp.Tests/Features/Products
mkdir -p tests/MyApp.Tests/Common
```

## Key Package Installations

### Application Project

```bash
cd src/MyApp

# MediatR for CQRS
dotnet add package MediatR

# EF Core (primary data access)
dotnet add package Microsoft.EntityFrameworkCore
dotnet add package Microsoft.EntityFrameworkCore.Design
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL   # or your provider

# Dapper for performance-critical queries
dotnet add package Dapper

# Validation
dotnet add package FluentValidation
dotnet add package FluentValidation.DependencyInjectionExtensions

# Carter (optional - endpoint organization alternative)
dotnet add package Carter
```

### Test Project

```bash
cd tests/MyApp.Tests

dotnet add package Microsoft.AspNetCore.Mvc.Testing
dotnet add package Testcontainers.PostgreSql          # real database in tests
dotnet add package Respawn                             # test data isolation
dotnet add package FluentAssertions
dotnet add package NSubstitute                         # mocking when needed
dotnet add package Bogus                               # test data generation
```

## Code Examples

### Domain Entity with Invariants

```csharp
// src/MyApp/Domain/Product.cs
namespace MyApp.Domain;

public class Product
{
    public Guid Id { get; private set; }
    public string Name { get; private set; } = string.Empty;
    public string Sku { get; private set; } = string.Empty;
    public decimal Price { get; private set; }
    public int StockQuantity { get; private set; }
    public DateTime CreatedAt { get; private set; }
    public DateTime? UpdatedAt { get; private set; }

    private Product() { } // EF Core constructor

    public static Product Create(string name, string sku, decimal price, int stockQuantity)
    {
        if (price <= 0)
            throw new ArgumentException("Price must be greater than zero.", nameof(price));

        if (stockQuantity < 0)
            throw new ArgumentException("Stock quantity cannot be negative.", nameof(stockQuantity));

        return new Product
        {
            Id = Guid.NewGuid(),
            Name = name,
            Sku = sku,
            Price = price,
            StockQuantity = stockQuantity,
            CreatedAt = DateTime.UtcNow
        };
    }

    public void AdjustStock(int quantity)
    {
        if (StockQuantity + quantity < 0)
            throw new InvalidOperationException("Insufficient stock.");

        StockQuantity += quantity;
        UpdatedAt = DateTime.UtcNow;
    }
}
```

### Complete Vertical Slice: CreateProduct

```csharp
// src/MyApp/Features/Products/CreateProduct.cs
using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using MyApp.Data;
using MyApp.Domain;

namespace MyApp.Features.Products;

// --- Endpoint ---
public static class CreateProductEndpoint
{
    public static void Map(IEndpointRouteBuilder app)
    {
        app.MapPost("/api/products", async (
            CreateProductCommand command,
            ISender sender,
            CancellationToken ct) =>
        {
            var result = await sender.Send(command, ct);
            return Results.Created($"/api/products/{result.Id}", result);
        })
        .WithName("CreateProduct")
        .WithTags("Products")
        .Produces<CreateProductResponse>(StatusCodes.Status201Created)
        .ProducesValidationProblem()
        .WithOpenApi();
    }
}

// --- Command ---
public record CreateProductCommand(
    string Name,
    string Sku,
    decimal Price,
    int StockQuantity) : IRequest<CreateProductResponse>;

// --- Response ---
public record CreateProductResponse(Guid Id, string Name, string Sku, decimal Price);

// --- Validator ---
public class CreateProductValidator : AbstractValidator<CreateProductCommand>
{
    public CreateProductValidator(AppDbContext db)
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(200);

        RuleFor(x => x.Sku)
            .NotEmpty()
            .MaximumLength(50)
            .MustAsync(async (sku, ct) =>
                !await db.Products.AnyAsync(p => p.Sku == sku, ct))
            .WithMessage("SKU already exists.");

        RuleFor(x => x.Price)
            .GreaterThan(0);

        RuleFor(x => x.StockQuantity)
            .GreaterThanOrEqualTo(0);
    }
}

// --- Handler ---
public class CreateProductHandler : IRequestHandler<CreateProductCommand, CreateProductResponse>
{
    private readonly AppDbContext _db;

    public CreateProductHandler(AppDbContext db)
    {
        _db = db;
    }

    public async Task<CreateProductResponse> Handle(
        CreateProductCommand request,
        CancellationToken cancellationToken)
    {
        var product = Product.Create(
            request.Name,
            request.Sku,
            request.Price,
            request.StockQuantity);

        _db.Products.Add(product);
        await _db.SaveChangesAsync(cancellationToken);

        return new CreateProductResponse(product.Id, product.Name, product.Sku, product.Price);
    }
}
```

### Query Slice with Dapper (Performance-Critical)

```csharp
// src/MyApp/Features/Products/ListProducts.cs
using Dapper;
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.EntityFrameworkCore;
using MyApp.Data;

namespace MyApp.Features.Products;

// --- Endpoint ---
public static class ListProductsEndpoint
{
    public static void Map(IEndpointRouteBuilder app)
    {
        app.MapGet("/api/products", async (
            [AsParameters] ListProductsQuery query,
            ISender sender,
            CancellationToken ct) =>
        {
            var result = await sender.Send(query, ct);
            return Results.Ok(result);
        })
        .WithName("ListProducts")
        .WithTags("Products")
        .Produces<PagedResult<ProductListItem>>()
        .WithOpenApi();
    }
}

// --- Query ---
public record ListProductsQuery(
    string? Search,
    int Page = 1,
    int PageSize = 20) : IRequest<PagedResult<ProductListItem>>;

// --- Response ---
public record ProductListItem(Guid Id, string Name, string Sku, decimal Price, int StockQuantity);
public record PagedResult<T>(IReadOnlyList<T> Items, int TotalCount, int Page, int PageSize);

// --- Handler (Dapper for read performance) ---
public sealed class ListProductsHandler(AppDbContext db)
    : IRequestHandler<ListProductsQuery, PagedResult<ProductListItem>>
{
    public async Task<PagedResult<ProductListItem>> Handle(
        ListProductsQuery request,
        CancellationToken cancellationToken)
    {
        var connection = db.Database.GetDbConnection();
        var offset = (request.Page - 1) * request.PageSize;

        const string countSql = """
            SELECT COUNT(*)
            FROM "Products"
            WHERE (@Search IS NULL OR "Name" ILIKE '%' || @Search || '%')
            """;

        const string dataSql = """
            SELECT "Id", "Name", "Sku", "Price", "StockQuantity"
            FROM "Products"
            WHERE (@Search IS NULL OR "Name" ILIKE '%' || @Search || '%')
            ORDER BY "CreatedAt" DESC
            LIMIT @PageSize OFFSET @Offset
            """;

        var parameters = new { request.Search, request.PageSize, Offset = offset };

        var totalCount = await connection.ExecuteScalarAsync<int>(countSql, parameters);
        var items = (await connection.QueryAsync<ProductListItem>(dataSql, parameters)).ToList();

        return new PagedResult<ProductListItem>(items, totalCount, request.Page, request.PageSize);
    }
}
```

### Custom Exceptions and ProblemDetails Middleware

```csharp
// src/MyApp/Common/Exceptions/AppException.cs
namespace MyApp.Common.Exceptions;

public abstract class AppException(string message) : Exception(message);
```

```csharp
// src/MyApp/Common/Exceptions/NotFoundException.cs
namespace MyApp.Common.Exceptions;

public sealed class NotFoundException : AppException
{
    public string EntityName { get; }
    public object Key { get; }

    public NotFoundException(string entityName, object key)
        : base($"{entityName} with key '{key}' was not found.")
    {
        EntityName = entityName;
        Key = key;
    }
}

// src/MyApp/Common/Exceptions/ConflictException.cs
namespace MyApp.Common.Exceptions;

public sealed class ConflictException(string message) : AppException(message);
```

```csharp
// src/MyApp/Common/Middleware/ExceptionHandlingMiddleware.cs
using System.Diagnostics;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using MyApp.Common.Exceptions;
using ValidationException = MyApp.Common.Exceptions.ValidationException;

namespace MyApp.Common.Middleware;

public class ExceptionHandlingMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionHandlingMiddleware> _logger;

    public ExceptionHandlingMiddleware(RequestDelegate next, ILogger<ExceptionHandlingMiddleware> logger)
    {
        _next = next;
        _logger = logger;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            await HandleExceptionAsync(context, ex);
        }
    }

    private async Task HandleExceptionAsync(HttpContext context, Exception exception)
    {
        var problemDetails = exception switch
        {
            NotFoundException notFound => new ProblemDetails
            {
                Status = StatusCodes.Status404NotFound,
                Title = "Resource Not Found",
                Detail = notFound.Message,
                Type = "https://tools.ietf.org/html/rfc9110#section-15.5.5"
            },
            ValidationException validation => new ProblemDetails
            {
                Status = StatusCodes.Status422UnprocessableEntity,
                Title = "Validation Failed",
                Detail = "One or more validation errors occurred.",
                Type = "https://tools.ietf.org/html/rfc9110#section-15.5.21",
                Extensions = { ["errors"] = validation.Errors }
            },
            ConflictException conflict => new ProblemDetails
            {
                Status = StatusCodes.Status409Conflict,
                Title = "Conflict",
                Detail = conflict.Message,
                Type = "https://tools.ietf.org/html/rfc9110#section-15.5.10"
            },
            _ => new ProblemDetails
            {
                Status = StatusCodes.Status500InternalServerError,
                Title = "Internal Server Error",
                Detail = "An unexpected error occurred.",
                Type = "https://tools.ietf.org/html/rfc9110#section-15.6.1"
            }
        };

        problemDetails.Extensions["traceId"] = Activity.Current?.Id ?? context.TraceIdentifier;

        _logger.LogError(exception, "Unhandled exception: {Message}", exception.Message);

        context.Response.StatusCode = problemDetails.Status ?? 500;
        await context.Response.WriteAsJsonAsync(problemDetails);
    }
}
```

### MediatR Pipeline: Validation Behavior

```csharp
// src/MyApp/Common/Behaviors/ValidationBehavior.cs
using FluentValidation;
using MediatR;
using ValidationException = MyApp.Common.Exceptions.ValidationException;

namespace MyApp.Common.Behaviors;

public class ValidationBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    private readonly IEnumerable<IValidator<TRequest>> _validators;

    public ValidationBehavior(IEnumerable<IValidator<TRequest>> validators)
    {
        _validators = validators;
    }

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        if (!_validators.Any())
            return await next();

        var context = new ValidationContext<TRequest>(request);

        var results = await Task.WhenAll(
            _validators.Select(v => v.ValidateAsync(context, cancellationToken)));

        var failures = results
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .ToList();

        if (failures.Count != 0)
        {
            var errors = failures
                .GroupBy(f => f.PropertyName)
                .ToDictionary(
                    g => g.Key,
                    g => g.Select(f => f.ErrorMessage).ToArray());

            throw new ValidationException(errors);
        }

        return await next();
    }
}
```

```csharp
// src/MyApp/Common/Exceptions/ValidationException.cs
namespace MyApp.Common.Exceptions;

public sealed class ValidationException : AppException
{
    public IDictionary<string, string[]> Errors { get; }

    public ValidationException(IDictionary<string, string[]> errors)
        : base("One or more validation errors occurred.")
    {
        Errors = errors;
    }
}
```

### MediatR Pipeline: Logging Behavior

```csharp
// src/MyApp/Common/Behaviors/LoggingBehavior.cs
using System.Diagnostics;
using MediatR;

namespace MyApp.Common.Behaviors;

public class LoggingBehavior<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    private readonly ILogger<LoggingBehavior<TRequest, TResponse>> _logger;

    public LoggingBehavior(ILogger<LoggingBehavior<TRequest, TResponse>> logger)
    {
        _logger = logger;
    }

    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        var requestName = typeof(TRequest).Name;
        _logger.LogInformation("Handling {RequestName}", requestName);

        var stopwatch = Stopwatch.StartNew();
        var response = await next();
        stopwatch.Stop();

        _logger.LogInformation("Handled {RequestName} in {ElapsedMs}ms",
            requestName, stopwatch.ElapsedMilliseconds);

        return response;
    }
}
```

### Extension Methods for DI Registration

```csharp
// src/MyApp/Common/Extensions/ServiceCollectionExtensions.cs
using FluentValidation;
using MediatR;
using Microsoft.EntityFrameworkCore;
using MyApp.Common.Behaviors;
using MyApp.Data;
using Npgsql;

namespace MyApp.Common.Extensions;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddApplicationServices(this IServiceCollection services)
    {
        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssemblyContaining<Program>();
            cfg.AddOpenBehavior(typeof(LoggingBehavior<,>));
            cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
        });

        services.AddValidatorsFromAssemblyContaining<Program>();

        return services;
    }

    public static IServiceCollection AddPersistence(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        var connectionString = configuration.GetConnectionString("Default")
            ?? throw new InvalidOperationException("Connection string 'Default' not found.");

        // EF Core for commands (PostgreSQL)
        // For SQL Server alternative: options.UseSqlServer(connectionString)
        services.AddDbContext<AppDbContext>(options =>
            options.UseNpgsql(connectionString));

        // For Dapper queries, inject AppDbContext and use its connection:
        // var connection = db.Database.GetDbConnection();
        // This ensures proper connection lifecycle management.
        // Alternatively, use NpgsqlDataSource (recommended for .NET 9):
        services.AddNpgsqlDataSource(connectionString);

        return services;
    }
}
```

### Feature Endpoint Registration

```csharp
// src/MyApp/Common/Extensions/WebApplicationExtensions.cs
using MyApp.Features.Products;
using MyApp.Features.Orders;

namespace MyApp.Common.Extensions;

public static class WebApplicationExtensions
{
    public static WebApplication MapFeatureEndpoints(this WebApplication app)
    {
        CreateProductEndpoint.Map(app);
        GetProductEndpoint.Map(app);
        ListProductsEndpoint.Map(app);
        UpdateProductEndpoint.Map(app);
        DeleteProductEndpoint.Map(app);

        CreateOrderEndpoint.Map(app);
        GetOrderEndpoint.Map(app);
        ListOrdersEndpoint.Map(app);

        return app;
    }
}
```

### Program.cs

```csharp
// src/MyApp/Program.cs
using MyApp.Common.Extensions;
using MyApp.Common.Middleware;

var builder = WebApplication.CreateBuilder(args);

// Service registration via extension methods
builder.Services.AddApplicationServices();
builder.Services.AddPersistence(builder.Configuration);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();
builder.Services.AddProblemDetails();

var app = builder.Build();

// Middleware pipeline
app.UseMiddleware<ExceptionHandlingMiddleware>();

if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

// Map all feature endpoints
app.MapFeatureEndpoints();

app.Run();

// Make Program accessible to WebApplicationFactory in tests
public partial class Program { }
```

### Carter Alternative for Endpoint Organization

Carter provides a module-based approach to grouping Minimal API endpoints per feature.

```csharp
// src/MyApp/Features/Products/ProductModule.cs
using Carter;
using MediatR;

namespace MyApp.Features.Products;

public class ProductModule : ICarterModule
{
    public void AddRoutes(IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/products").WithTags("Products");

        group.MapPost("/", async (CreateProductCommand command, ISender sender, CancellationToken ct) =>
        {
            var result = await sender.Send(command, ct);
            return Results.Created($"/api/products/{result.Id}", result);
        })
        .WithName("CreateProduct")
        .Produces<CreateProductResponse>(StatusCodes.Status201Created)
        .ProducesValidationProblem();

        group.MapGet("/", async ([AsParameters] ListProductsQuery query, ISender sender, CancellationToken ct) =>
        {
            var result = await sender.Send(query, ct);
            return Results.Ok(result);
        })
        .WithName("ListProducts")
        .Produces<PagedResult<ProductListItem>>();

        group.MapGet("/{id:guid}", async (Guid id, ISender sender, CancellationToken ct) =>
        {
            var result = await sender.Send(new GetProductQuery(id), ct);
            return Results.Ok(result);
        })
        .WithName("GetProduct")
        .Produces<ProductDetailResponse>()
        .ProducesProblem(StatusCodes.Status404NotFound);
    }
}
```

When using Carter, register it in Program.cs instead of manual endpoint mapping:

```csharp
// In Program.cs
builder.Services.AddCarter();
// ...
app.MapCarter(); // replaces app.MapFeatureEndpoints()
```

### AppDbContext

```csharp
// src/MyApp/Data/AppDbContext.cs
using Microsoft.EntityFrameworkCore;
using MyApp.Domain;

namespace MyApp.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<Product> Products => Set<Product>();
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }
}
```

## Testing Strategy

Vertical Slice Architecture favors integration tests that exercise the full pipeline (HTTP request through MediatR to database and back). Unit tests are reserved for complex domain logic.

### Test Infrastructure

```csharp
// tests/MyApp.Tests/Common/TestWebApplicationFactory.cs
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using MyApp.Data;
using Npgsql;
using Testcontainers.PostgreSql;

namespace MyApp.Tests.Common;

public class TestWebApplicationFactory : WebApplicationFactory<Program>, IAsyncLifetime
{
    private readonly PostgreSqlContainer _dbContainer = new PostgreSqlBuilder()
        .WithImage("postgres:16-alpine")
        .Build();

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureServices(services =>
        {
            // Remove the existing DbContext registration
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<AppDbContext>));

            if (descriptor is not null)
                services.Remove(descriptor);

            // Register test database backed by Testcontainers
            services.AddDbContext<AppDbContext>(options =>
                options.UseNpgsql(_dbContainer.GetConnectionString()));

            // Also replace Dapper data source for test database
            var dataSourceDescriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(NpgsqlDataSource));
            if (dataSourceDescriptor is not null)
                services.Remove(dataSourceDescriptor);

            services.AddNpgsqlDataSource(_dbContainer.GetConnectionString());
        });
    }

    public async Task InitializeAsync()
    {
        await _dbContainer.StartAsync();

        // Apply migrations
        using var scope = Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        await db.Database.MigrateAsync();
    }

    public new async Task DisposeAsync()
    {
        await _dbContainer.DisposeAsync();
    }
}
```

```csharp
// tests/MyApp.Tests/Common/TestDatabaseFixture.cs
using Microsoft.EntityFrameworkCore;
using MyApp.Data;
using Respawn;

namespace MyApp.Tests.Common;

public class TestDatabaseFixture : IAsyncLifetime
{
    private readonly TestWebApplicationFactory _factory;
    private Respawner _respawner = default!;

    public HttpClient Client { get; private set; } = default!;

    public TestDatabaseFixture(TestWebApplicationFactory factory)
    {
        _factory = factory;
    }

    public async Task InitializeAsync()
    {
        Client = _factory.CreateClient();

        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var connection = db.Database.GetDbConnection();
        await connection.OpenAsync();

        _respawner = await Respawner.CreateAsync(connection, new RespawnerOptions
        {
            DbAdapter = DbAdapter.Postgres,
            SchemasToInclude = ["public"]
        });
    }

    public async Task ResetDatabaseAsync()
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var connection = db.Database.GetDbConnection();
        await connection.OpenAsync();
        await _respawner.ResetAsync(connection);
    }

    public Task DisposeAsync() => Task.CompletedTask;
}
```

### Integration Tests: Full Slice Through HTTP

```csharp
// tests/MyApp.Tests/Features/Products/CreateProductTests.cs
using System.Net;
using System.Net.Http.Json;
using FluentAssertions;
using MyApp.Features.Products;
using MyApp.Tests.Common;

namespace MyApp.Tests.Features.Products;

public class CreateProductTests : IClassFixture<TestWebApplicationFactory>, IAsyncLifetime
{
    private readonly TestDatabaseFixture _fixture;

    public CreateProductTests(TestWebApplicationFactory factory)
    {
        _fixture = new TestDatabaseFixture(factory);
    }

    public Task InitializeAsync() => _fixture.InitializeAsync();
    public Task DisposeAsync() => _fixture.ResetDatabaseAsync();

    [Fact]
    public async Task CreateProduct_WithValidData_Returns201AndProduct()
    {
        // Arrange
        var command = new CreateProductCommand(
            Name: "Widget",
            Sku: "WDG-001",
            Price: 29.99m,
            StockQuantity: 100);

        // Act
        var response = await _fixture.Client.PostAsJsonAsync("/api/products", command);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);

        var product = await response.Content.ReadFromJsonAsync<CreateProductResponse>();
        product.Should().NotBeNull();
        product!.Name.Should().Be("Widget");
        product.Sku.Should().Be("WDG-001");
        product.Price.Should().Be(29.99m);

        response.Headers.Location!.ToString().Should().Contain(product.Id.ToString());
    }

    [Fact]
    public async Task CreateProduct_WithDuplicateSku_Returns422()
    {
        // Arrange - create first product
        var first = new CreateProductCommand("Widget A", "WDG-DUP", 10m, 5);
        await _fixture.Client.PostAsJsonAsync("/api/products", first);

        // Act - attempt duplicate SKU
        var duplicate = new CreateProductCommand("Widget B", "WDG-DUP", 20m, 10);
        var response = await _fixture.Client.PostAsJsonAsync("/api/products", duplicate);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
    }

    [Theory]
    [InlineData("", "SKU-1", 10, 0)]       // empty name
    [InlineData("Widget", "", 10, 0)]       // empty SKU
    [InlineData("Widget", "SKU-1", -1, 0)]  // negative price
    [InlineData("Widget", "SKU-1", 10, -5)] // negative stock
    public async Task CreateProduct_WithInvalidData_Returns422(
        string name, string sku, decimal price, int stock)
    {
        var command = new CreateProductCommand(name, sku, price, stock);

        var response = await _fixture.Client.PostAsJsonAsync("/api/products", command);

        response.StatusCode.Should().Be(HttpStatusCode.UnprocessableEntity);
    }
}
```

### Unit Test for Domain Invariants

```csharp
// tests/MyApp.Tests/Domain/ProductTests.cs
using FluentAssertions;
using MyApp.Domain;

namespace MyApp.Tests.Domain;

public class ProductTests
{
    [Fact]
    public void Create_WithNegativePrice_ThrowsArgumentException()
    {
        var act = () => Product.Create("Widget", "SKU-1", -10m, 5);

        act.Should().Throw<ArgumentException>()
            .WithParameterName("price");
    }

    [Fact]
    public void AdjustStock_BelowZero_ThrowsInvalidOperationException()
    {
        var product = Product.Create("Widget", "SKU-1", 10m, 3);

        var act = () => product.AdjustStock(-5);

        act.Should().Throw<InvalidOperationException>()
            .WithMessage("*Insufficient stock*");
    }
}
```

## Architecture Decision Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Project organization | Feature folders | Each slice is self-contained, reduces merge conflicts |
| CQRS mediator | MediatR | Decouples endpoint from handler, enables pipeline behaviors |
| Data access (writes) | EF Core directly in handler | No repository abstraction; handler owns its data access |
| Data access (reads) | Dapper for perf-critical | Raw SQL performance without ORM overhead for list queries |
| Validation | FluentValidation + MediatR pipeline | Automatic validation before handler executes |
| Error handling | ProblemDetails (RFC 9457) | Standardized error responses with structured detail |
| Endpoint grouping | Static Map methods or Carter modules | Feature-local endpoint registration |
| Testing emphasis | Integration tests via WebApplicationFactory | Tests the real pipeline end-to-end, catches wiring issues |
| Test database | Testcontainers (PostgreSQL) | Real database behavior, no in-memory fakes |
| Test isolation | Respawn | Fast database reset between tests without recreation |

## Next Steps

1. Define domain entities and their invariants
2. Create the `AppDbContext` with EF Core configurations
3. Generate initial migration with `dotnet ef migrations add InitialCreate`
4. Build the first vertical slice (endpoint + command + handler + validator)
5. Wire up MediatR pipeline behaviors (validation, logging)
6. Add exception handling middleware with ProblemDetails
7. Write integration tests for the first slice using WebApplicationFactory
8. Repeat for each feature -- each slice is independent
