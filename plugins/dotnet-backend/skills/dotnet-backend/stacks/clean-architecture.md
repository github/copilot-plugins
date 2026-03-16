# Clean Architecture Stack

## Overview

Clean Architecture enforces strict dependency inversion through concentric layers where source code dependencies point inward. The domain sits at the center with zero outward dependencies, application logic orchestrates use cases, infrastructure adapts to external concerns, and the API layer handles HTTP transport. This stack uses .NET 9, MediatR for CQRS, EF Core as the primary data layer (no repository pattern), and FluentValidation in the MediatR pipeline.

## When to Choose Clean Architecture

**Best for:**
- Large teams (3+ developers) where strict boundaries prevent coupling drift
- Long-lived products (2+ year horizon) where maintainability outweighs initial velocity
- Domains with complex business rules that benefit from isolation
- Systems requiring independent deployability of layers
- Projects where multiple UI surfaces consume the same application logic

**Avoid when:**
- Small CRUD applications with thin business logic (use Vertical Slice instead)
- Rapid prototyping or MVPs where speed to market is the primary constraint
- Solo developer or two-person teams where the ceremony adds overhead without benefit
- Microservices that are already small and focused on a single bounded context

## Solution Structure

```
MyApp/
  MyApp.sln
  src/
    MyApp.Domain/
      Entities/
      ValueObjects/
      Enums/
      Events/
      Exceptions/
      MyApp.Domain.csproj
    MyApp.Application/
      Common/
        Behaviors/
        Interfaces/
        Models/
      Features/
        Orders/
          Commands/
            CreateOrder/
              CreateOrderCommand.cs
              CreateOrderCommandHandler.cs
              CreateOrderCommandValidator.cs
          Queries/
            GetOrder/
              GetOrderQuery.cs
              GetOrderQueryHandler.cs
              OrderDto.cs
      DependencyInjection.cs
      MyApp.Application.csproj
    MyApp.Infrastructure/
      Persistence/
        ApplicationDbContext.cs
        Configurations/
        Interceptors/
        Migrations/
      Services/
      DapperQueries/
      DependencyInjection.cs
      MyApp.Infrastructure.csproj
    MyApp.WebApi/
      Endpoints/
      Controllers/
      Middleware/
      Filters/
      Program.cs
      MyApp.WebApi.csproj
  tests/
    MyApp.Domain.UnitTests/
    MyApp.Application.UnitTests/
    MyApp.Infrastructure.IntegrationTests/
    MyApp.WebApi.IntegrationTests/
```

## Scaffolding Commands

Run these commands from the root directory where you want the solution created.

### Create Solution and Projects

```bash
# Create solution
dotnet new sln -n MyApp
mkdir -p src tests

# Create projects
dotnet new classlib -n MyApp.Domain -o src/MyApp.Domain -f net9.0
dotnet new classlib -n MyApp.Application -o src/MyApp.Application -f net9.0
dotnet new classlib -n MyApp.Infrastructure -o src/MyApp.Infrastructure -f net9.0
dotnet new webapi -n MyApp.WebApi -o src/MyApp.WebApi -f net9.0 --use-controllers false

# Create test projects
dotnet new xunit -n MyApp.Domain.UnitTests -o tests/MyApp.Domain.UnitTests -f net9.0
dotnet new xunit -n MyApp.Application.UnitTests -o tests/MyApp.Application.UnitTests -f net9.0
dotnet new xunit -n MyApp.Infrastructure.IntegrationTests -o tests/MyApp.Infrastructure.IntegrationTests -f net9.0
dotnet new xunit -n MyApp.WebApi.IntegrationTests -o tests/MyApp.WebApi.IntegrationTests -f net9.0

# Add all projects to solution
dotnet sln add src/MyApp.Domain/MyApp.Domain.csproj
dotnet sln add src/MyApp.Application/MyApp.Application.csproj
dotnet sln add src/MyApp.Infrastructure/MyApp.Infrastructure.csproj
dotnet sln add src/MyApp.WebApi/MyApp.WebApi.csproj
dotnet sln add tests/MyApp.Domain.UnitTests/MyApp.Domain.UnitTests.csproj
dotnet sln add tests/MyApp.Application.UnitTests/MyApp.Application.UnitTests.csproj
dotnet sln add tests/MyApp.Infrastructure.IntegrationTests/MyApp.Infrastructure.IntegrationTests.csproj
dotnet sln add tests/MyApp.WebApi.IntegrationTests/MyApp.WebApi.IntegrationTests.csproj
```

### Project References (Dependency Rule)

Dependencies always point inward. Domain has zero references. Nothing ever references WebApi.

```bash
# Application depends on Domain
dotnet add src/MyApp.Application reference src/MyApp.Domain

# Infrastructure depends on Application and Domain
dotnet add src/MyApp.Infrastructure reference src/MyApp.Application
dotnet add src/MyApp.Infrastructure reference src/MyApp.Domain

# WebApi depends on Application and Infrastructure (for DI wiring only)
dotnet add src/MyApp.WebApi reference src/MyApp.Application
dotnet add src/MyApp.WebApi reference src/MyApp.Infrastructure

# Test project references
dotnet add tests/MyApp.Domain.UnitTests reference src/MyApp.Domain
dotnet add tests/MyApp.Application.UnitTests reference src/MyApp.Application
dotnet add tests/MyApp.Application.UnitTests reference src/MyApp.Domain
dotnet add tests/MyApp.Infrastructure.IntegrationTests reference src/MyApp.Infrastructure
dotnet add tests/MyApp.Infrastructure.IntegrationTests reference src/MyApp.Application
dotnet add tests/MyApp.WebApi.IntegrationTests reference src/MyApp.WebApi
```

### Package Installations

```bash
# Domain: zero NuGet packages (pure C#, no framework dependencies)

# Application
dotnet add src/MyApp.Application package MediatR
dotnet add src/MyApp.Application package FluentValidation
dotnet add src/MyApp.Application package FluentValidation.DependencyInjectionExtensions

# Infrastructure
dotnet add src/MyApp.Infrastructure package Microsoft.EntityFrameworkCore
dotnet add src/MyApp.Infrastructure package Microsoft.EntityFrameworkCore.SqlServer
dotnet add src/MyApp.Infrastructure package Microsoft.EntityFrameworkCore.Tools
dotnet add src/MyApp.Infrastructure package Dapper
dotnet add src/MyApp.Infrastructure package Microsoft.Data.SqlClient
dotnet add src/MyApp.Infrastructure package Microsoft.Extensions.Caching.StackExchangeRedis
dotnet add src/MyApp.Infrastructure package Microsoft.Extensions.Http.Resilience

# WebApi
dotnet add src/MyApp.WebApi package Asp.Versioning.Http
dotnet add src/MyApp.WebApi package Asp.Versioning.Mvc.ApiExplorer
dotnet add src/MyApp.WebApi package Microsoft.AspNetCore.OpenApi
dotnet add src/MyApp.WebApi package Swashbuckle.AspNetCore

# Test projects
dotnet add tests/MyApp.Application.UnitTests package NSubstitute
dotnet add tests/MyApp.Application.UnitTests package FluentAssertions
dotnet add tests/MyApp.Application.UnitTests package AutoFixture
dotnet add tests/MyApp.Infrastructure.IntegrationTests package Testcontainers.MsSql
dotnet add tests/MyApp.Infrastructure.IntegrationTests package Microsoft.EntityFrameworkCore.InMemory
dotnet add tests/MyApp.Infrastructure.IntegrationTests package FluentAssertions
dotnet add tests/MyApp.WebApi.IntegrationTests package Microsoft.AspNetCore.Mvc.Testing
dotnet add tests/MyApp.WebApi.IntegrationTests package FluentAssertions
dotnet add tests/MyApp.WebApi.IntegrationTests package Testcontainers.MsSql
```

### Create Folder Structure

```bash
# Domain
mkdir -p src/MyApp.Domain/{Entities,ValueObjects,Enums,Events,Exceptions}

# Application
mkdir -p src/MyApp.Application/Common/{Behaviors,Interfaces,Models}
mkdir -p src/MyApp.Application/Features

# Infrastructure
mkdir -p src/MyApp.Infrastructure/Persistence/{Configurations,Interceptors,Migrations}
mkdir -p src/MyApp.Infrastructure/{Services,DapperQueries}

# WebApi
mkdir -p src/MyApp.WebApi/{Endpoints,Controllers,Middleware,Filters}
```

## Code Examples

### Domain Layer: Entity with Domain Events

The domain layer contains pure C# with no framework dependencies. Entities enforce their own invariants.

```csharp
// src/MyApp.Domain/Entities/Order.cs
using MediatR;
using MyApp.Domain.Enums;
using MyApp.Domain.Events;
using MyApp.Domain.Exceptions;

namespace MyApp.Domain.Entities;

public sealed class Order
{
    private readonly List<OrderItem> _items = [];

    public Guid Id { get; private set; }
    public string CustomerEmail { get; private set; } = default!;
    public OrderStatus Status { get; private set; }
    public DateTime CreatedAt { get; private set; }
    public IReadOnlyCollection<OrderItem> Items => _items.AsReadOnly();
    public decimal TotalAmount => _items.Sum(i => i.Price * i.Quantity);

    private readonly List<INotification> _domainEvents = [];
    public IReadOnlyCollection<INotification> DomainEvents => _domainEvents.AsReadOnly();

    private Order() { } // EF Core constructor

    public static Order Create(string customerEmail)
    {
        if (string.IsNullOrWhiteSpace(customerEmail))
            throw new DomainException("Customer email is required.");

        var order = new Order
        {
            Id = Guid.NewGuid(),
            CustomerEmail = customerEmail,
            Status = OrderStatus.Draft,
            CreatedAt = DateTime.UtcNow
        };

        order._domainEvents.Add(new OrderCreatedEvent(order.Id));
        return order;
    }

    public void AddItem(string productName, decimal price, int quantity)
    {
        if (Status != OrderStatus.Draft)
            throw new DomainException("Can only add items to draft orders.");
        if (quantity <= 0)
            throw new DomainException("Quantity must be positive.");

        _items.Add(new OrderItem(productName, price, quantity));
    }

    public void Submit()
    {
        if (_items.Count == 0)
            throw new DomainException("Cannot submit an empty order.");

        Status = OrderStatus.Submitted;
        _domainEvents.Add(new OrderSubmittedEvent(Id, TotalAmount));
    }

    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

```csharp
// src/MyApp.Domain/Entities/OrderItem.cs
namespace MyApp.Domain.Entities;

public sealed class OrderItem
{
    public Guid Id { get; private set; }
    public string ProductName { get; private set; } = default!;
    public decimal Price { get; private set; }
    public int Quantity { get; private set; }

    private OrderItem() { } // EF Core

    public OrderItem(string productName, decimal price, int quantity)
    {
        Id = Guid.NewGuid();
        ProductName = productName;
        Price = price;
        Quantity = quantity;
    }
}
```

```csharp
// src/MyApp.Domain/Enums/OrderStatus.cs
namespace MyApp.Domain.Enums;

public enum OrderStatus
{
    Draft,
    Submitted,
    Confirmed,
    Shipped,
    Delivered,
    Cancelled
}
```

```csharp
// src/MyApp.Domain/Events/OrderCreatedEvent.cs
using MediatR;

namespace MyApp.Domain.Events;

public sealed record OrderCreatedEvent(Guid OrderId) : INotification;
```

```csharp
// src/MyApp.Domain/Events/OrderSubmittedEvent.cs
using MediatR;

namespace MyApp.Domain.Events;

public sealed record OrderSubmittedEvent(Guid OrderId, decimal TotalAmount) : INotification;
```

```csharp
// src/MyApp.Domain/Exceptions/AppException.cs
namespace MyApp.Domain.Exceptions;

public abstract class AppException : Exception
{
    protected AppException(string message) : base(message) { }
}

// src/MyApp.Domain/Exceptions/DomainException.cs
namespace MyApp.Domain.Exceptions;

public sealed class DomainException : AppException
{
    public DomainException(string message) : base(message) { }
}
```

### Application Layer: CQRS with MediatR

Commands mutate state. Queries read state. Handlers orchestrate the work.

```csharp
// src/MyApp.Application/Common/Interfaces/IApplicationDbContext.cs
using Microsoft.EntityFrameworkCore;
using MyApp.Domain.Entities;

namespace MyApp.Application.Common.Interfaces;

public interface IApplicationDbContext
{
    DbSet<Order> Orders { get; }
    DbSet<OrderItem> OrderItems { get; }

    Task<int> SaveChangesAsync(CancellationToken cancellationToken = default);
}
```

```csharp
// src/MyApp.Application/Features/Orders/Commands/CreateOrder/CreateOrderCommand.cs
using MediatR;

namespace MyApp.Application.Features.Orders.Commands.CreateOrder;

public sealed record CreateOrderCommand(
    string CustomerEmail,
    List<OrderItemDto> Items
) : IRequest<Guid>;

public sealed record OrderItemDto(
    string ProductName,
    decimal Price,
    int Quantity
);
```

```csharp
// src/MyApp.Application/Features/Orders/Commands/CreateOrder/CreateOrderCommandValidator.cs
using FluentValidation;

namespace MyApp.Application.Features.Orders.Commands.CreateOrder;

public sealed class CreateOrderCommandValidator : AbstractValidator<CreateOrderCommand>
{
    public CreateOrderCommandValidator()
    {
        RuleFor(x => x.CustomerEmail)
            .NotEmpty()
            .EmailAddress();

        RuleFor(x => x.Items)
            .NotEmpty()
            .WithMessage("Order must contain at least one item.");

        RuleForEach(x => x.Items).ChildRules(item =>
        {
            item.RuleFor(i => i.ProductName).NotEmpty();
            item.RuleFor(i => i.Price).GreaterThan(0);
            item.RuleFor(i => i.Quantity).GreaterThan(0);
        });
    }
}
```

```csharp
// src/MyApp.Application/Features/Orders/Commands/CreateOrder/CreateOrderCommandHandler.cs
using MediatR;
using MyApp.Application.Common.Interfaces;
using MyApp.Domain.Entities;

namespace MyApp.Application.Features.Orders.Commands.CreateOrder;

public sealed class CreateOrderCommandHandler(
    IApplicationDbContext dbContext
) : IRequestHandler<CreateOrderCommand, Guid>
{
    public async Task<Guid> Handle(
        CreateOrderCommand request,
        CancellationToken cancellationToken)
    {
        var order = Order.Create(request.CustomerEmail);

        foreach (var item in request.Items)
        {
            order.AddItem(item.ProductName, item.Price, item.Quantity);
        }

        order.Submit();

        dbContext.Orders.Add(order);
        await dbContext.SaveChangesAsync(cancellationToken);

        return order.Id;
    }
}
```

```csharp
// src/MyApp.Application/Features/Orders/Queries/GetOrder/GetOrderQuery.cs
using MediatR;
using MyApp.Application.Features.Orders.Commands.CreateOrder;

namespace MyApp.Application.Features.Orders.Queries.GetOrder;

public sealed record GetOrderQuery(Guid OrderId) : IRequest<OrderDetailDto?>;

public sealed record OrderDetailDto(
    Guid Id,
    string CustomerEmail,
    string Status,
    decimal TotalAmount,
    DateTime CreatedAt,
    List<OrderItemDto> Items
);
```

```csharp
// src/MyApp.Application/Features/Orders/Queries/GetOrder/GetOrderQueryHandler.cs
using MediatR;
using Microsoft.EntityFrameworkCore;
using MyApp.Application.Common.Interfaces;
using MyApp.Application.Features.Orders.Commands.CreateOrder;

namespace MyApp.Application.Features.Orders.Queries.GetOrder;

public sealed class GetOrderQueryHandler(
    IApplicationDbContext dbContext
) : IRequestHandler<GetOrderQuery, OrderDetailDto?>
{
    public async Task<OrderDetailDto?> Handle(
        GetOrderQuery request,
        CancellationToken cancellationToken)
    {
        return await dbContext.Orders
            .Where(o => o.Id == request.OrderId)
            .Select(o => new OrderDetailDto(
                o.Id,
                o.CustomerEmail,
                o.Status.ToString(),
                o.TotalAmount,
                o.CreatedAt,
                o.Items.Select(i => new OrderItemDto(
                    i.ProductName, i.Price, i.Quantity
                )).ToList()
            ))
            .FirstOrDefaultAsync(cancellationToken);
    }
}
```

### FluentValidation Pipeline Behavior

This MediatR pipeline behavior intercepts every request and runs matching validators before the handler executes. Validation failures throw a custom `ValidationException` that the exception middleware converts to ProblemDetails.

```csharp
// src/MyApp.Application/Common/Behaviors/ValidationBehavior.cs
using FluentValidation;
using MediatR;

namespace MyApp.Application.Common.Behaviors;

public sealed class ValidationBehavior<TRequest, TResponse>(
    IEnumerable<IValidator<TRequest>> validators
) : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    public async Task<TResponse> Handle(
        TRequest request,
        RequestHandlerDelegate<TResponse> next,
        CancellationToken cancellationToken)
    {
        if (!validators.Any())
            return await next(cancellationToken);

        var context = new ValidationContext<TRequest>(request);

        var validationResults = await Task.WhenAll(
            validators.Select(v => v.ValidateAsync(context, cancellationToken)));

        var failures = validationResults
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .ToList();

        if (failures.Count != 0)
            throw new Application.Common.Exceptions.ValidationException(failures);

        return await next(cancellationToken);
    }
}
```

```csharp
// src/MyApp.Application/Common/Exceptions/ValidationException.cs
using FluentValidation.Results;
using MyApp.Domain.Exceptions;

namespace MyApp.Application.Common.Exceptions;

public sealed class ValidationException : AppException
{
    public IDictionary<string, string[]> Errors { get; }

    public ValidationException(IEnumerable<ValidationFailure> failures)
        : base("One or more validation failures occurred.")
    {
        Errors = failures
            .GroupBy(e => e.PropertyName, e => e.ErrorMessage)
            .ToDictionary(g => g.Key, g => g.ToArray());
    }
}
```

```csharp
// src/MyApp.Application/Common/Exceptions/NotFoundException.cs
using MyApp.Domain.Exceptions;

namespace MyApp.Application.Common.Exceptions;

public sealed class NotFoundException : AppException
{
    public NotFoundException(string entityName, object key)
        : base($"Entity \"{entityName}\" ({key}) was not found.") { }
}
```

### Application DI Registration

```csharp
// src/MyApp.Application/DependencyInjection.cs
using System.Reflection;
using FluentValidation;
using MediatR;
using Microsoft.Extensions.DependencyInjection;
using MyApp.Application.Common.Behaviors;

namespace MyApp.Application;

public static class DependencyInjection
{
    public static IServiceCollection AddApplication(this IServiceCollection services)
    {
        var assembly = Assembly.GetExecutingAssembly();

        services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(assembly);
            cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
        });

        services.AddValidatorsFromAssembly(assembly);

        return services;
    }
}
```

### Infrastructure Layer: EF Core (No Repository Pattern)

DbContext IS the abstraction. It implements the application-layer interface directly. No wrapping repositories.

```csharp
// src/MyApp.Infrastructure/Persistence/ApplicationDbContext.cs
using Microsoft.EntityFrameworkCore;
using MyApp.Application.Common.Interfaces;
using MyApp.Domain.Entities;

namespace MyApp.Infrastructure.Persistence;

public sealed class ApplicationDbContext(
    DbContextOptions<ApplicationDbContext> options
) : DbContext(options), IApplicationDbContext
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(
            typeof(ApplicationDbContext).Assembly);
    }
}
```

```csharp
// src/MyApp.Infrastructure/Persistence/Configurations/OrderConfiguration.cs
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using MyApp.Domain.Entities;

namespace MyApp.Infrastructure.Persistence.Configurations;

public sealed class OrderConfiguration : IEntityTypeConfiguration<Order>
{
    public void Configure(EntityTypeBuilder<Order> builder)
    {
        builder.HasKey(o => o.Id);

        builder.Property(o => o.CustomerEmail)
            .HasMaxLength(256)
            .IsRequired();

        builder.Property(o => o.Status)
            .HasConversion<string>()
            .HasMaxLength(50);

        builder.HasMany(o => o.Items)
            .WithOne()
            .HasForeignKey("OrderId")
            .OnDelete(DeleteBehavior.Cascade);

        // Ignore domain events — they are not persisted
        builder.Ignore(o => o.DomainEvents);

        builder.HasIndex(o => o.CustomerEmail);
        builder.HasIndex(o => o.Status);
    }
}
```

```csharp
// src/MyApp.Infrastructure/Persistence/Configurations/OrderItemConfiguration.cs
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;
using MyApp.Domain.Entities;

namespace MyApp.Infrastructure.Persistence.Configurations;

public sealed class OrderItemConfiguration : IEntityTypeConfiguration<OrderItem>
{
    public void Configure(EntityTypeBuilder<OrderItem> builder)
    {
        builder.HasKey(i => i.Id);
        builder.Property(i => i.ProductName).HasMaxLength(200).IsRequired();
        builder.Property(i => i.Price).HasPrecision(18, 2);
        builder.Property(i => i.Quantity).IsRequired();
    }
}
```

### Infrastructure: Dapper for Performance-Critical Queries

Use Dapper alongside EF Core when you need raw SQL performance for read-heavy or reporting scenarios.

```csharp
// src/MyApp.Infrastructure/DapperQueries/OrderSummaryQuery.cs
using Dapper;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.Configuration;

namespace MyApp.Infrastructure.DapperQueries;

public sealed record OrderSummaryResult(
    Guid OrderId,
    string CustomerEmail,
    decimal TotalAmount,
    int ItemCount,
    DateTime CreatedAt
);

public sealed class OrderSummaryQuery(IConfiguration configuration)
{
    public async Task<IEnumerable<OrderSummaryResult>> GetRecentOrdersAsync(
        int count,
        CancellationToken cancellationToken = default)
    {
        const string sql = """
            SELECT TOP (@Count)
                o.Id AS OrderId,
                o.CustomerEmail,
                SUM(oi.Price * oi.Quantity) AS TotalAmount,
                COUNT(oi.Id) AS ItemCount,
                o.CreatedAt
            FROM Orders o
            LEFT JOIN OrderItems oi ON oi.OrderId = o.Id
            GROUP BY o.Id, o.CustomerEmail, o.CreatedAt
            ORDER BY o.CreatedAt DESC
            """;

        await using var connection = new SqlConnection(
            configuration.GetConnectionString("Default"));

        return await connection.QueryAsync<OrderSummaryResult>(
            new CommandDefinition(sql, new { Count = count }, cancellationToken: cancellationToken));
    }
}
```

### Infrastructure DI Registration

```csharp
// src/MyApp.Infrastructure/DependencyInjection.cs
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using MyApp.Application.Common.Interfaces;
using MyApp.Infrastructure.DapperQueries;
using MyApp.Infrastructure.Persistence;

namespace MyApp.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddInfrastructure(
        this IServiceCollection services,
        IConfiguration configuration)
    {
        services.AddDbContext<ApplicationDbContext>(options =>
            options.UseSqlServer(
                configuration.GetConnectionString("Default"),
                b => b.MigrationsAssembly(typeof(ApplicationDbContext).Assembly.FullName)));

        services.AddScoped<IApplicationDbContext>(provider =>
            provider.GetRequiredService<ApplicationDbContext>());

        // Dapper queries
        services.AddScoped<OrderSummaryQuery>();

        return services;
    }
}
```

### WebApi Layer: ProblemDetails Exception Middleware

RFC 9457 ProblemDetails provides a standard, machine-readable error format. Map each custom exception to the appropriate HTTP status code.

```csharp
// src/MyApp.WebApi/Middleware/ExceptionHandlingMiddleware.cs
using Microsoft.AspNetCore.Mvc;
using MyApp.Application.Common.Exceptions;
using MyApp.Domain.Exceptions;

namespace MyApp.WebApi.Middleware;

public sealed class ExceptionHandlingMiddleware(
    RequestDelegate next,
    ILogger<ExceptionHandlingMiddleware> logger)
{
    public async Task InvokeAsync(HttpContext httpContext)
    {
        try
        {
            await next(httpContext);
        }
        catch (Exception ex)
        {
            await HandleExceptionAsync(httpContext, ex);
        }
    }

    private async Task HandleExceptionAsync(HttpContext httpContext, Exception exception)
    {
        logger.LogError(exception, "Unhandled exception: {Message}", exception.Message);

        var problemDetails = exception switch
        {
            ValidationException validationEx => new ValidationProblemDetails(validationEx.Errors)
            {
                Status = StatusCodes.Status422UnprocessableEntity,
                Title = "Validation Failed",
                Type = "https://tools.ietf.org/html/rfc9110#section-15.5.1"
            },
            NotFoundException => new ProblemDetails
            {
                Status = StatusCodes.Status404NotFound,
                Title = "Not Found",
                Detail = exception.Message,
                Type = "https://tools.ietf.org/html/rfc9110#section-15.5.5"
            },
            DomainException => new ProblemDetails
            {
                Status = StatusCodes.Status409Conflict,
                Title = "Domain Rule Violation",
                Detail = exception.Message,
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

        httpContext.Response.StatusCode = problemDetails.Status ?? 500;
        await httpContext.Response.WriteAsJsonAsync(problemDetails);
    }
}
```

### WebApi Layer: Minimal API Endpoints

Minimal APIs are the recommended approach for new .NET 9 projects. Group endpoints by feature using extension methods.

```csharp
// src/MyApp.WebApi/Endpoints/OrderEndpoints.cs
using MediatR;
using MyApp.Application.Features.Orders.Commands.CreateOrder;
using MyApp.Application.Features.Orders.Queries.GetOrder;

namespace MyApp.WebApi.Endpoints;

public static class OrderEndpoints
{
    public static RouteGroupBuilder MapOrderEndpoints(this IEndpointRouteBuilder routes)
    {
        var group = routes.MapGroup("/api/v{version:apiVersion}/orders")
            .WithTags("Orders")
            .WithOpenApi();

        group.MapPost("/", async (CreateOrderCommand command, ISender sender) =>
        {
            var orderId = await sender.Send(command);
            return Results.Created($"/api/v1/orders/{orderId}", new { id = orderId });
        })
        .WithName("CreateOrder")
        .Produces<object>(StatusCodes.Status201Created)
        .ProducesValidationProblem(StatusCodes.Status422UnprocessableEntity);

        group.MapGet("/{id:guid}", async (Guid id, ISender sender) =>
        {
            var order = await sender.Send(new GetOrderQuery(id));
            return order is not null ? Results.Ok(order) : Results.NotFound();
        })
        .WithName("GetOrder")
        .Produces<OrderDetailDto>()
        .ProducesProblem(StatusCodes.Status404NotFound);

        return group;
    }
}
```

### WebApi Layer: Controller Alternative

Use controllers when the team prefers convention-based routing, needs complex model binding, or has an existing controller-based codebase.

```csharp
// src/MyApp.WebApi/Controllers/OrdersController.cs
using Asp.Versioning;
using MediatR;
using Microsoft.AspNetCore.Mvc;
using MyApp.Application.Features.Orders.Commands.CreateOrder;
using MyApp.Application.Features.Orders.Queries.GetOrder;

namespace MyApp.WebApi.Controllers;

[ApiController]
[ApiVersion("1.0")]
[Route("api/v{version:apiVersion}/[controller]")]
public sealed class OrdersController(ISender sender) : ControllerBase
{
    [HttpPost]
    [ProducesResponseType(StatusCodes.Status201Created)]
    [ProducesResponseType(typeof(ValidationProblemDetails), StatusCodes.Status422UnprocessableEntity)]
    public async Task<IActionResult> Create(
        CreateOrderCommand command,
        CancellationToken cancellationToken)
    {
        var orderId = await sender.Send(command, cancellationToken);
        return CreatedAtAction(nameof(Get), new { id = orderId }, new { id = orderId });
    }

    [HttpGet("{id:guid}")]
    [ProducesResponseType(typeof(OrderDetailDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<IActionResult> Get(
        Guid id,
        CancellationToken cancellationToken)
    {
        var order = await sender.Send(new GetOrderQuery(id), cancellationToken);
        return order is not null ? Ok(order) : NotFound();
    }
}
```

**Minimal APIs vs Controllers trade-offs:**

| Concern | Minimal APIs | Controllers |
|---------|-------------|-------------|
| Performance | Slightly faster (less middleware) | Negligible difference in practice |
| Discoverability | Explicit registration required | Convention-based automatic discovery |
| Testing | Test endpoint delegates directly | Well-established testing patterns |
| Model binding | Manual for complex scenarios | Rich attribute-based binding |
| Filters | Endpoint filters (newer API) | Action filters (mature ecosystem) |
| Team familiarity | Newer pattern | Familiar to most .NET developers |

### Program.cs Setup

```csharp
// src/MyApp.WebApi/Program.cs
using Asp.Versioning;
using MyApp.Application;
using MyApp.Infrastructure;
using MyApp.WebApi.Endpoints;
using MyApp.WebApi.Middleware;

var builder = WebApplication.CreateBuilder(args);

// Layer registration via extension methods
builder.Services.AddApplication();
builder.Services.AddInfrastructure(builder.Configuration);

// API versioning
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
    options.ApiVersionReader = new UrlSegmentApiVersionReader();
})
.AddApiExplorer(options =>
{
    options.GroupNameFormat = "'v'VVV";
    options.SubstituteApiVersionInUrl = true;
});

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

// Map endpoints
var versionSet = app.NewApiVersionSet()
    .HasApiVersion(new ApiVersion(1, 0))
    .Build();

app.MapOrderEndpoints()
    .WithApiVersionSet(versionSet)
    .MapToApiVersion(new ApiVersion(1, 0));

app.Run();

// Required for WebApplicationFactory in integration tests
public partial class Program;
```

## Testing Strategy

Clean Architecture yields the highest return on unit tests because domain and application layers are pure logic with clear boundaries.

### Domain Unit Tests (Pure Logic, No Mocks)

Domain tests validate business rules. They require zero mocking because the domain has no dependencies.

```csharp
// tests/MyApp.Domain.UnitTests/Entities/OrderTests.cs
using MyApp.Domain.Entities;
using MyApp.Domain.Enums;
using MyApp.Domain.Exceptions;

namespace MyApp.Domain.UnitTests.Entities;

public sealed class OrderTests
{
    [Fact]
    public void Create_WithValidEmail_ShouldSetDraftStatus()
    {
        var order = Order.Create("test@example.com");

        Assert.Equal(OrderStatus.Draft, order.Status);
        Assert.Single(order.DomainEvents);
    }

    [Fact]
    public void Submit_WithNoItems_ShouldThrowDomainException()
    {
        var order = Order.Create("test@example.com");

        var exception = Assert.Throws<DomainException>(() => order.Submit());
        Assert.Equal("Cannot submit an empty order.", exception.Message);
    }

    [Fact]
    public void AddItem_ToSubmittedOrder_ShouldThrowDomainException()
    {
        var order = Order.Create("test@example.com");
        order.AddItem("Widget", 10.00m, 1);
        order.Submit();

        Assert.Throws<DomainException>(() =>
            order.AddItem("Gadget", 5.00m, 2));
    }

    [Fact]
    public void TotalAmount_ShouldSumAllItems()
    {
        var order = Order.Create("test@example.com");
        order.AddItem("Widget", 10.00m, 2);
        order.AddItem("Gadget", 5.00m, 3);

        Assert.Equal(35.00m, order.TotalAmount);
    }
}
```

### Application Unit Tests (Mock IApplicationDbContext)

Handler tests mock the DbContext interface. Validate that handlers orchestrate correctly.

```csharp
// tests/MyApp.Application.UnitTests/Features/Orders/CreateOrderCommandHandlerTests.cs
using NSubstitute;
using MyApp.Application.Common.Interfaces;
using MyApp.Application.Features.Orders.Commands.CreateOrder;
using MyApp.Domain.Entities;
using Microsoft.EntityFrameworkCore;

namespace MyApp.Application.UnitTests.Features.Orders;

public sealed class CreateOrderCommandHandlerTests
{
    private readonly IApplicationDbContext _dbContext = Substitute.For<IApplicationDbContext>();
    private readonly CreateOrderCommandHandler _handler;

    public CreateOrderCommandHandlerTests()
    {
        _dbContext.Orders.Returns(Substitute.For<DbSet<Order>>());
        _handler = new CreateOrderCommandHandler(_dbContext);
    }

    [Fact]
    public async Task Handle_WithValidCommand_ShouldReturnOrderId()
    {
        var command = new CreateOrderCommand(
            "test@example.com",
            [new OrderItemDto("Widget", 10.00m, 2)]
        );

        var result = await _handler.Handle(command, CancellationToken.None);

        Assert.NotEqual(Guid.Empty, result);
        await _dbContext.Received(1).SaveChangesAsync(Arg.Any<CancellationToken>());
    }
}
```

### Infrastructure Integration Tests (Testcontainers + Real DB)

Test EF Core configurations against a real database in a container.

```csharp
// tests/MyApp.Infrastructure.IntegrationTests/Persistence/ApplicationDbContextTests.cs
using Microsoft.EntityFrameworkCore;
using MyApp.Domain.Entities;
using MyApp.Infrastructure.Persistence;
using Testcontainers.MsSql;

namespace MyApp.Infrastructure.IntegrationTests.Persistence;

public sealed class ApplicationDbContextTests : IAsyncLifetime
{
    private readonly MsSqlContainer _container = new MsSqlBuilder()
        .WithImage("mcr.microsoft.com/mssql/server:2022-latest")
        .Build();

    private ApplicationDbContext _dbContext = default!;

    public async Task InitializeAsync()
    {
        await _container.StartAsync();

        var options = new DbContextOptionsBuilder<ApplicationDbContext>()
            .UseSqlServer(_container.GetConnectionString())
            .Options;

        _dbContext = new ApplicationDbContext(options);
        await _dbContext.Database.EnsureCreatedAsync();
    }

    public async Task DisposeAsync()
    {
        await _dbContext.DisposeAsync();
        await _container.DisposeAsync();
    }

    [Fact]
    public async Task SaveOrder_ShouldPersistWithItems()
    {
        var order = Order.Create("test@example.com");
        order.AddItem("Widget", 10.00m, 2);

        _dbContext.Orders.Add(order);
        await _dbContext.SaveChangesAsync();

        var loaded = await _dbContext.Orders
            .Include(o => o.Items)
            .FirstAsync(o => o.Id == order.Id);

        Assert.Equal("test@example.com", loaded.CustomerEmail);
        Assert.Single(loaded.Items);
    }
}
```

### WebApi Integration Tests (WebApplicationFactory)

End-to-end HTTP tests against the full middleware pipeline.

```csharp
// tests/MyApp.WebApi.IntegrationTests/OrderEndpointTests.cs
using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using MyApp.Infrastructure.Persistence;
using Testcontainers.MsSql;

namespace MyApp.WebApi.IntegrationTests;

public sealed class OrderEndpointTests : IAsyncLifetime
{
    private readonly MsSqlContainer _container = new MsSqlBuilder()
        .WithImage("mcr.microsoft.com/mssql/server:2022-latest")
        .Build();

    private WebApplicationFactory<Program> _factory = default!;
    private HttpClient _client = default!;

    public async Task InitializeAsync()
    {
        await _container.StartAsync();

        _factory = new WebApplicationFactory<Program>()
            .WithWebHostBuilder(builder =>
            {
                builder.ConfigureServices(services =>
                {
                    // Replace the DB with the container instance
                    var descriptor = services.SingleOrDefault(
                        d => d.ServiceType == typeof(DbContextOptions<ApplicationDbContext>));
                    if (descriptor is not null) services.Remove(descriptor);

                    services.AddDbContext<ApplicationDbContext>(options =>
                        options.UseSqlServer(_container.GetConnectionString()));
                });
            });

        _client = _factory.CreateClient();

        // Ensure DB is created
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        await db.Database.EnsureCreatedAsync();
    }

    public async Task DisposeAsync()
    {
        _client.Dispose();
        await _factory.DisposeAsync();
        await _container.DisposeAsync();
    }

    [Fact]
    public async Task CreateOrder_WithValidPayload_ShouldReturn201()
    {
        var payload = new
        {
            CustomerEmail = "test@example.com",
            Items = new[]
            {
                new { ProductName = "Widget", Price = 10.00m, Quantity = 2 }
            }
        };

        var response = await _client.PostAsJsonAsync("/api/v1/orders", payload);

        Assert.Equal(HttpStatusCode.Created, response.StatusCode);
    }

    [Fact]
    public async Task CreateOrder_WithInvalidEmail_ShouldReturn422()
    {
        var payload = new
        {
            CustomerEmail = "not-an-email",
            Items = new[]
            {
                new { ProductName = "Widget", Price = 10.00m, Quantity = 2 }
            }
        };

        var response = await _client.PostAsJsonAsync("/api/v1/orders", payload);

        Assert.Equal(HttpStatusCode.UnprocessableEntity, response.StatusCode);
    }

    [Fact]
    public async Task GetOrder_WithNonExistentId_ShouldReturn404()
    {
        var response = await _client.GetAsync($"/api/v1/orders/{Guid.NewGuid()}");

        Assert.Equal(HttpStatusCode.NotFound, response.StatusCode);
    }
}
```

## Testing Ratios for Clean Architecture

| Layer | Test Type | Volume | Why |
|-------|-----------|--------|-----|
| Domain | Unit tests | High | Pure logic, fast, no setup cost |
| Application | Unit tests | High | Handler orchestration, validation rules |
| Infrastructure | Integration tests | Medium | EF configs, Dapper queries against real DB |
| WebApi | Integration tests | Low-Medium | HTTP pipeline, routing, serialization |

The dependency rule means domain and application tests run in milliseconds with zero infrastructure. This is why Clean Architecture produces more unit tests than other patterns.

## Key Design Decisions

**No Repository Pattern**: EF Core's `DbContext` already implements Unit of Work and provides `DbSet<T>` as a collection-like abstraction. Adding a repository layer on top introduces indirection with no benefit. The `IApplicationDbContext` interface gives you testability. Query handlers project directly from `DbSet<T>` using LINQ.

**FluentValidation in Pipeline + Domain Invariants**: Two levels of validation serve different purposes. FluentValidation in the MediatR pipeline validates input shape (email format, required fields, string lengths). Domain entities validate business invariants (cannot submit empty order, cannot add items to submitted order). Pipeline validation returns 422. Domain violations return 409.

**MediatR for CQRS**: Separates read and write paths at the application layer. Commands go through validation pipeline and mutate state. Queries can bypass heavy behaviors and project DTOs directly. This separation allows independent optimization of each path.

**Dapper for Performance-Critical Reads**: EF Core is the primary data access tool. Dapper is used selectively for reporting queries, dashboard aggregations, or any read path where EF Core's overhead is measurable. Do not default to Dapper; reach for it when profiling shows a need.

**ProblemDetails (RFC 9457)**: A single exception middleware maps all custom exceptions to standard HTTP problem responses. Consumers get consistent, machine-readable error payloads across every endpoint.
