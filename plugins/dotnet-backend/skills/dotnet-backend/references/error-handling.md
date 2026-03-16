# Error Handling Patterns - .NET 9

## 1. Exception Hierarchy

Define a base exception and typed subclasses. The global middleware maps each type to an HTTP status code.

```csharp
using System.Collections.ObjectModel;

public abstract class AppException(string message) : Exception(message);

public sealed class NotFoundException : AppException
{
    public NotFoundException(string entity, object key)
        : base($"{entity} with key '{key}' was not found.") { }
}

public sealed class ConflictException : AppException
{
    public ConflictException(string message) : base(message) { }
}

public sealed class ValidationException : AppException
{
    public IReadOnlyDictionary<string, string[]> Errors { get; }

    public ValidationException(IReadOnlyDictionary<string, string[]> errors)
        : base("One or more validation errors occurred.")
    {
        Errors = errors;
    }
}

public sealed class ForbiddenException : AppException
{
    public ForbiddenException(string? message = null)
        : base(message ?? "You do not have permission to perform this action.") { }
}
```

## 2. ProblemDetails Middleware

Implement `IExceptionHandler` (.NET 9) to map each exception type to a ProblemDetails response that follows RFC 9457.

```csharp
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;

public sealed class GlobalExceptionHandler : IExceptionHandler
{
    private readonly IProblemDetailsService _problemDetailsService;
    private readonly ILogger<GlobalExceptionHandler> _logger;

    public GlobalExceptionHandler(
        IProblemDetailsService problemDetailsService,
        ILogger<GlobalExceptionHandler> logger)
    {
        _problemDetailsService = problemDetailsService;
        _logger = logger;
    }

    public async ValueTask<bool> TryHandleAsync(
        HttpContext httpContext,
        Exception exception,
        CancellationToken cancellationToken)
    {
        _logger.LogError(exception, "Unhandled exception: {Message}", exception.Message);

        var problemDetails = exception switch
        {
            NotFoundException ex => new ProblemDetails
            {
                Status = StatusCodes.Status404NotFound,
                Title = "Resource Not Found",
                Detail = ex.Message,
                Type = "https://tools.ietf.org/html/rfc9110#section-15.5.5"
            },
            ConflictException ex => new ProblemDetails
            {
                Status = StatusCodes.Status409Conflict,
                Title = "Conflict",
                Detail = ex.Message,
                Type = "https://tools.ietf.org/html/rfc9110#section-15.5.10"
            },
            ValidationException ex => CreateValidationProblemDetails(ex),
            ForbiddenException ex => new ProblemDetails
            {
                Status = StatusCodes.Status403Forbidden,
                Title = "Forbidden",
                Detail = ex.Message,
                Type = "https://tools.ietf.org/html/rfc9110#section-15.5.4"
            },
            _ => new ProblemDetails
            {
                Status = StatusCodes.Status500InternalServerError,
                Title = "Internal Server Error",
                Detail = "An unexpected error occurred.",
                Type = "https://tools.ietf.org/html/rfc9110#section-15.6.1"
            }
        };

        problemDetails.Instance = httpContext.Request.Path;
        problemDetails.Extensions["traceId"] = httpContext.TraceIdentifier;

        httpContext.Response.StatusCode = problemDetails.Status ?? 500;

        return await _problemDetailsService.TryWriteAsync(
            new ProblemDetailsContext
            {
                HttpContext = httpContext,
                ProblemDetails = problemDetails
            });
    }

    private static ProblemDetails CreateValidationProblemDetails(ValidationException ex)
    {
        var problem = new ProblemDetails
        {
            Status = StatusCodes.Status422UnprocessableEntity,
            Title = "Validation Failed",
            Detail = ex.Message,
            Type = "https://tools.ietf.org/html/rfc9110#section-15.5.21"
        };
        problem.Extensions["errors"] = ex.Errors;
        return problem;
    }
}
```

## 3. FluentValidation Integration

A MediatR pipeline behavior that runs all registered validators before the handler executes. Validation failures are collected and thrown as a single `ValidationException`.

```csharp
using System.Collections.ObjectModel;
using FluentValidation;
using MediatR;

public sealed class ValidationBehavior<TRequest, TResponse>
    : IPipelineBehavior<TRequest, TResponse>
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

        var context = new FluentValidation.ValidationContext<TRequest>(request);

        var results = await Task.WhenAll(
            _validators.Select(v => v.ValidateAsync(context, cancellationToken)));

        var errors = results
            .SelectMany(r => r.Errors)
            .Where(f => f is not null)
            .GroupBy(f => f.PropertyName)
            .ToDictionary(
                g => g.Key,
                g => g.Select(f => f.ErrorMessage).ToArray());

        if (errors.Count > 0)
            throw new ValidationException(
                new ReadOnlyDictionary<string, string[]>(errors));

        return await next();
    }
}
```

## 4. Domain Invariant Enforcement

Use a `Guard` utility with static methods to enforce domain rules inside entity constructors and methods. Failures throw domain-level exceptions that the middleware catches.

```csharp
using System;

public static class Guard
{
    public static string AgainstNullOrWhiteSpace(string? value, string paramName)
    {
        if (string.IsNullOrWhiteSpace(value))
            throw new ArgumentException($"{paramName} must not be empty.", paramName);
        return value;
    }

    public static T AgainstNull<T>(T? value, string paramName) where T : class
    {
        ArgumentNullException.ThrowIfNull(value, paramName);
        return value;
    }

    public static decimal AgainstNegativeOrZero(decimal value, string paramName)
    {
        if (value <= 0)
            throw new ArgumentOutOfRangeException(paramName, $"{paramName} must be positive.");
        return value;
    }
}

// Usage in an entity constructor:
public sealed class Order
{
    public Guid Id { get; }
    public string CustomerEmail { get; }
    public decimal Quantity { get; }

    public Order(Guid id, string customerEmail, decimal quantity)
    {
        Id = id == Guid.Empty ? Guid.NewGuid() : id;
        CustomerEmail = Guard.AgainstNullOrWhiteSpace(customerEmail, nameof(customerEmail));
        Quantity = Guard.AgainstNegativeOrZero(quantity, nameof(quantity));
    }
}
```

## 5. Consistent API Error Responses

Every error response follows the RFC 9457 ProblemDetails shape. Below are example JSON payloads for each error type.

**404 Not Found**
```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.5",
  "title": "Resource Not Found",
  "status": 404,
  "detail": "Order with key '7a1c3e00-...' was not found.",
  "instance": "/api/orders/7a1c3e00-...",
  "traceId": "00-abc123-def456-01"
}
```

**422 Validation Failed**
```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.21",
  "title": "Validation Failed",
  "status": 422,
  "detail": "One or more validation errors occurred.",
  "instance": "/api/orders",
  "traceId": "00-abc123-def456-01",
  "errors": {
    "CustomerEmail": ["CustomerEmail must not be empty."],
    "Quantity": ["Quantity must be greater than zero."]
  }
}
```

**409 Conflict**
```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.10",
  "title": "Conflict",
  "status": 409,
  "detail": "An order with the same reference already exists.",
  "instance": "/api/orders",
  "traceId": "00-abc123-def456-01"
}
```

**403 Forbidden**
```json
{
  "type": "https://tools.ietf.org/html/rfc9110#section-15.5.4",
  "title": "Forbidden",
  "status": 403,
  "detail": "You do not have permission to perform this action.",
  "instance": "/api/orders/7a1c3e00-.../cancel",
  "traceId": "00-abc123-def456-01"
}
```

## 6. Program.cs Setup

Wire everything together in `Program.cs`. Order matters: `UseExceptionHandler` must appear before routing.

```csharp
using FluentValidation;

var builder = WebApplication.CreateBuilder(args);

// Register ProblemDetails services (RFC 9457 support)
builder.Services.AddProblemDetails();

// Register the global exception handler
builder.Services.AddExceptionHandler<GlobalExceptionHandler>();

// Register MediatR with the validation pipeline behavior
builder.Services.AddMediatR(cfg =>
{
    cfg.RegisterServicesFromAssembly(typeof(Program).Assembly);
    cfg.AddOpenBehavior(typeof(ValidationBehavior<,>));
});

// Register all FluentValidation validators from the assembly
builder.Services.AddValidatorsFromAssemblyContaining<Program>();

var app = builder.Build();

// Global exception handling middleware (must precede routing)
app.UseExceptionHandler();

// Return ProblemDetails for bare status codes (e.g. 401, 404 from framework)
app.UseStatusCodePages();

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

app.Run();
```
