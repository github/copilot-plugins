# Architecture-Specific Testing Strategies (.NET 9)

## Testing Strategy by Architecture

### Clean Architecture

Emphasize **unit tests** for domain and application layers. The domain layer is pure C# with no
infrastructure dependencies, making it trivially testable. The application layer uses interfaces
(ports) that are easily substituted with NSubstitute.

- **Domain Layer**: Direct unit tests, no mocks needed. Test value objects, entities, domain services, and domain events.
- **Application Layer**: Unit test MediatR handlers by mocking `DbContext` or interface dependencies via NSubstitute.
- **Infrastructure/API Layer**: Thin integration tests via `WebApplicationFactory` to verify wiring.
- **Ratio**: ~60% unit, ~30% integration, ~10% E2E.

### Vertical Slice Architecture

Emphasize **integration tests** that exercise the full slice through the HTTP pipeline. Each
feature is a self-contained vertical cut, so testing at the HTTP boundary gives the highest
confidence-to-effort ratio.

- **Primary approach**: `WebApplicationFactory` + real database via Testcontainers + Respawn for state reset.
- **Unit tests only for**: Complex domain logic extracted into pure functions or domain models.
- **Ratio**: ~20% unit, ~70% integration, ~10% E2E.

### Modular Monolith

Test **within modules** using integration tests and **across modules** using contract tests.
Each module exposes a public API (typically via MediatR notifications or explicit contracts)
that neighboring modules depend on.

- **Intra-module**: Full integration tests per module with isolated database schemas.
- **Cross-module**: Contract tests verifying published events and shared DTOs remain compatible.
- **Ratio**: ~30% unit, ~50% integration, ~20% contract/E2E.

---

## Core Testing Stack

| Package               | Purpose                                      |
|-----------------------|----------------------------------------------|
| `xUnit`               | Test framework with parallel execution        |
| `FluentAssertions`    | Readable assertion syntax                     |
| `NSubstitute`         | Mocking/stubbing interfaces                   |
| `Testcontainers`      | Disposable PostgreSQL/SQL Server in Docker     |
| `Respawn`             | Fast database state reset between tests        |
| `Bogus`               | Realistic fake data generation                 |
| `WebApplicationFactory` | In-process HTTP testing without network overhead |

---

## Code Examples

### WebApplicationFactory with Testcontainers

```csharp
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.TestHost;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Testcontainers.PostgreSql;

public class AppFactory : WebApplicationFactory<Program>, IAsyncLifetime
{
    private readonly PostgreSqlContainer _dbContainer = new PostgreSqlBuilder()
        .WithImage("postgres:16-alpine")
        .WithDatabase("testdb")
        .WithUsername("test")
        .WithPassword("test")
        .Build();

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.ConfigureTestServices(services =>
        {
            // Remove the production DbContext registration
            var descriptor = services.SingleOrDefault(
                d => d.ServiceType == typeof(DbContextOptions<AppDbContext>));
            if (descriptor is not null)
                services.Remove(descriptor);

            // Register test DbContext pointing at the container
            services.AddDbContext<AppDbContext>(options =>
                options.UseNpgsql(_dbContainer.GetConnectionString()));
        });
    }

    public async Task InitializeAsync()
    {
        await _dbContainer.StartAsync();

        // Apply migrations once on startup
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

### Respawn Checkpoint per Test Class

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Respawn;
using Respawn.Graph;

public abstract class IntegrationTestBase : IClassFixture<AppFactory>, IAsyncLifetime
{
    private readonly AppFactory _factory;
    private Respawner _respawner = default!;
    protected HttpClient Client { get; private set; } = default!;

    protected IntegrationTestBase(AppFactory factory)
    {
        _factory = factory;
    }

    public async Task InitializeAsync()
    {
        Client = _factory.CreateClient();

        // Build respawner against the running container
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var connection = db.Database.GetDbConnection();
        await connection.OpenAsync();

        _respawner = await Respawner.CreateAsync(connection, new RespawnerOptions
        {
            DbAdapter = DbAdapter.Postgres,
            SchemasToInclude = ["public"],
            TablesToIgnore = [new Table("__EFMigrationsHistory")]
        });
    }

    public async Task DisposeAsync()
    {
        // Reset database state after each test class
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var connection = db.Database.GetDbConnection();
        await connection.OpenAsync();
        await _respawner.ResetAsync(connection);
    }

    protected async Task<T> SeedAsync<T>(T entity) where T : class
    {
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        db.Set<T>().Add(entity);
        await db.SaveChangesAsync();
        return entity;
    }
}
```

### Domain Unit Test (Clean Architecture)

```csharp
using FluentAssertions;
using Xunit;

public class OrderTests
{
    [Fact]
    public void AddItem_WithValidProduct_ShouldIncreaseTotal()
    {
        // Arrange
        var order = Order.Create(customerId: Guid.NewGuid());
        var product = new ProductSnapshot("SKU-001", "Widget", price: 25.00m);

        // Act
        order.AddItem(product, quantity: 3);

        // Assert
        order.Items.Should().HaveCount(1);
        order.Total.Should().Be(75.00m);
    }

    [Fact]
    public void AddItem_ExceedingMaxQuantity_ShouldThrowDomainException()
    {
        // Arrange
        var order = Order.Create(customerId: Guid.NewGuid());
        var product = new ProductSnapshot("SKU-001", "Widget", price: 10.00m);

        // Act
        var act = () => order.AddItem(product, quantity: 10_001);

        // Assert
        act.Should().Throw<DomainException>()
            .WithMessage("*exceeds maximum*");
    }
}
```

### MediatR Handler Unit Test with NSubstitute

```csharp
using FluentAssertions;
using MediatR;
using Microsoft.EntityFrameworkCore;
using NSubstitute;
using Xunit;

public class CreateOrderHandlerTests
{
    private readonly AppDbContext _db;
    private readonly IPublisher _publisher;
    private readonly CreateOrderHandler _sut;

    public CreateOrderHandlerTests()
    {
        // NOTE: In-memory provider is acceptable for isolated handler unit tests.
        // For integration tests, always use Testcontainers with a real database.
        var options = new DbContextOptionsBuilder<AppDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options;

        _db = new AppDbContext(options);
        _publisher = Substitute.For<IPublisher>();
        _sut = new CreateOrderHandler(_db, _publisher);
    }

    [Fact]
    public async Task Handle_ValidCommand_ShouldPersistOrderAndPublishEvent()
    {
        // Arrange
        var command = new CreateOrderCommand(
            CustomerId: Guid.NewGuid(),
            Items: [new OrderItemDto("SKU-001", 2)]);

        // Act
        var result = await _sut.Handle(command, CancellationToken.None);

        // Assert
        result.OrderId.Should().NotBeEmpty();

        var persisted = await _db.Orders.FindAsync(result.OrderId);
        persisted.Should().NotBeNull();
        persisted!.Items.Should().HaveCount(1);

        await _publisher.Received(1).Publish(
            Arg.Is<OrderCreatedEvent>(e => e.OrderId == result.OrderId),
            Arg.Any<CancellationToken>());
    }
}
```

### Full Integration Test through HTTP Endpoint (Vertical Slice)

```csharp
using System.Net;
using System.Net.Http.Json;
using FluentAssertions;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Xunit;

public class CreateOrderEndpointTests(AppFactory factory) : IntegrationTestBase(factory)
{
    [Fact]
    public async Task POST_Orders_WithValidPayload_ShouldReturn201()
    {
        // Arrange
        var customer = await SeedAsync(new CustomerFaker().Generate());

        var payload = new
        {
            CustomerId = customer.Id,
            Items = new[] { new { Sku = "SKU-001", Quantity = 2 } }
        };

        // Act
        var response = await Client.PostAsJsonAsync("/api/orders", payload);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.Created);

        var body = await response.Content.ReadFromJsonAsync<CreateOrderResponse>();
        body.Should().NotBeNull();
        body!.OrderId.Should().NotBeEmpty();

        // Verify side effects in the real database
        using var scope = _factory.Services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var order = await db.Orders
            .Include(o => o.Items)
            .FirstOrDefaultAsync(o => o.Id == body.OrderId);

        order.Should().NotBeNull();
        order!.Items.Should().HaveCount(1);
    }

    [Fact]
    public async Task POST_Orders_WithEmptyItems_ShouldReturn400()
    {
        // Arrange
        var payload = new { CustomerId = Guid.NewGuid(), Items = Array.Empty<object>() };

        // Act
        var response = await Client.PostAsJsonAsync("/api/orders", payload);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }
}
```

### Bogus Data Builder Pattern

```csharp
using Bogus;

public sealed class CustomerFaker : Faker<Customer>
{
    public CustomerFaker()
    {
        CustomInstantiator(f => Customer.Create(
            name: f.Person.FullName,
            email: f.Internet.Email()));

        // Deterministic seed for reproducible test runs
        UseSeed(42);
    }
}

public sealed class OrderFaker : Faker<Order>
{
    public OrderFaker(Guid? customerId = null)
    {
        CustomInstantiator(f =>
        {
            var order = Order.Create(customerId ?? Guid.NewGuid());
            var itemCount = f.Random.Int(1, 5);
            for (var i = 0; i < itemCount; i++)
            {
                order.AddItem(
                    new ProductSnapshot(
                        f.Commerce.Ean13(),
                        f.Commerce.ProductName(),
                        decimal.Parse(f.Commerce.Price(1, 500))),
                    quantity: f.Random.Int(1, 10));
            }
            return order;
        });
    }
}
```

---

## Test Organization

### Naming Convention

```
MethodUnderTest_Scenario_ExpectedBehavior
```

Examples: `AddItem_WithValidProduct_ShouldIncreaseTotal`, `Handle_DuplicateEmail_ShouldReturnConflict`.

### Arrange/Act/Assert

Every test method follows the three-section structure with explicit comment markers. Keep each
section focused: Arrange sets up state, Act performs exactly one action, Assert verifies outcomes.

### Shared Fixtures with IAsyncLifetime

Use `IClassFixture<T>` for expensive resources shared across a test class (database containers,
HTTP clients). Use `IAsyncLifetime` for setup/teardown that requires async operations. Never share
mutable state between test methods -- use Respawn or fresh seeds instead.

### Project Structure

```
tests/
  Unit/
    Domain/
      OrderTests.cs
    Application/
      Handlers/
        CreateOrderHandlerTests.cs
  Integration/
    Fixtures/
      AppFactory.cs
      IntegrationTestBase.cs
    Endpoints/
      CreateOrderEndpointTests.cs
  Fakers/
    CustomerFaker.cs
    OrderFaker.cs
```

---

## Common Pitfalls

### 1. Testing Implementation Details

Do not assert on internal method calls or private state. Test observable behavior: return values,
persisted state, published events, HTTP responses. If a refactor breaks your tests but not the
behavior, your tests are coupled to implementation.

### 2. Over-Mocking EF Core

Do not mock `DbSet<T>` or `IQueryable<T>`. EF Core's in-memory provider or a real database via
Testcontainers are both superior options. Mocked LINQ queries do not test actual SQL translation
and give false confidence. Use `InMemoryDatabase` for fast handler unit tests and Testcontainers
for integration tests that must verify query correctness.

### 3. Shared Mutable State Between Tests

Tests that depend on data seeded by other tests are fragile and order-dependent. Always use
Respawn to reset state, or seed required data within each test method. Never rely on test
execution order.

### 4. Ignoring the Test Pyramid per Architecture

Clean Architecture projects that skip domain unit tests and only write integration tests
waste CI time. Vertical Slice projects that mock everything instead of testing the full slice
miss wiring bugs. Match your testing strategy to your architecture.

### 5. Not Testing Failure Paths

Every endpoint and handler should have tests for validation failures, not-found cases, and
concurrency conflicts. Use `FluentAssertions` to verify error response shapes and status codes,
not just the happy path.
