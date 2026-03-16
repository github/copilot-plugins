# DDD Tactical Patterns in C# (.NET 9)

## 1. When DDD Is Worth It -- Decision Tree

| Domain Complexity | Approach | What You Use |
|---|---|---|
| **High** -- complex rules, many invariants, evolving logic | Full DDD | Aggregates, value objects, domain events, specifications |
| **Moderate** -- some business rules, mostly data-oriented | Lightweight DDD | Value objects + domain events only |
| **Low** -- pure CRUD, forms-over-data, admin panels | Anemic models | DTOs, EF Core entities with public setters, no domain layer |

**Rule of thumb:** "Save this form to the database" = skip DDD. "But only when" / "unless" / "depending on the state" = you need DDD.

---

## 2. Aggregate Design

- Aggregate root is the consistency boundary and only entry point.
- Keep aggregates small. Reference other aggregates by ID, not object reference.
- One transaction = one aggregate.
- Enforce all invariants inside aggregate methods. Never expose public setters.

```csharp
public sealed class Order : AuditableEntity<OrderId>
{
    private readonly List<OrderItem> _items = [];
    public CustomerId CustomerId { get; private set; }
    public OrderStatus Status { get; private set; }
    public Money TotalAmount { get; private set; }
    public IReadOnlyList<OrderItem> Items => _items.AsReadOnly();
    private Order() { } // EF Core constructor

    public static Order Create(CustomerId customerId)
    {
        var order = new Order
        {
            Id = OrderId.New(), CustomerId = customerId,
            Status = OrderStatus.Draft, TotalAmount = Money.Zero("USD")
        };
        order.AddDomainEvent(new OrderCreatedEvent(order.Id));
        return order;
    }

    public void AddItem(ProductId productId, int quantity, Money unitPrice)
    {
        if (Status != OrderStatus.Draft)
            throw new DomainException("Cannot modify a non-draft order.");
        if (quantity <= 0)
            throw new DomainException("Quantity must be positive.");

        var existing = _items.FirstOrDefault(i => i.ProductId == productId);
        if (existing is not null) existing.IncreaseQuantity(quantity);
        else _items.Add(new OrderItem(productId, quantity, unitPrice));
        RecalculateTotal();
    }

    public void Submit()
    {
        if (Status != OrderStatus.Draft)
            throw new DomainException("Only draft orders can be submitted.");
        if (_items.Count == 0)
            throw new DomainException("Cannot submit an order with no items.");
        Status = OrderStatus.Submitted;
        AddDomainEvent(new OrderSubmittedEvent(Id, CustomerId, TotalAmount));
    }

    private void RecalculateTotal() =>
        TotalAmount = _items.Select(i => i.Total)
            .Aggregate(Money.Zero("USD"), (acc, m) => acc + m);
}
```

---

## 3. Value Objects

Use C# `record` types -- structural equality, immutability, and concise syntax for free.

```csharp
using System;

public sealed record Money(decimal Amount, string Currency)
{
    public static Money Zero(string currency) => new(0m, currency);
    public static Money operator +(Money left, Money right)
    {
        if (left.Currency != right.Currency)
            throw new DomainException("Cannot add money with different currencies.");
        return new Money(left.Amount + right.Amount, left.Currency);
    }
    public static Money operator *(Money money, int qty) => new(money.Amount * qty, money.Currency);
}

public sealed record Address(string Street, string City, string State, string ZipCode, string Country);

public sealed record Email
{
    public string Value { get; }
    public Email(string value)
    {
        if (string.IsNullOrWhiteSpace(value) || !value.Contains('@'))
            throw new DomainException($"'{value}' is not a valid email address.");
        Value = value.Trim().ToLowerInvariant();
    }
}
```

---

## 4. Domain Events

Use MediatR `INotification`. Collect events during the operation, dispatch after `SaveChanges` succeeds.

```csharp
using MediatR;

public sealed record OrderSubmittedEvent(
    OrderId OrderId, CustomerId CustomerId, Money TotalAmount) : INotification;

public interface IHasDomainEvents
{
    IReadOnlyList<INotification> DomainEvents { get; }
    void ClearDomainEvents();
}

public abstract class Entity<TId> : IHasDomainEvents where TId : notnull
{
    public TId Id { get; protected set; } = default!;
    private readonly List<INotification> _domainEvents = [];
    public IReadOnlyList<INotification> DomainEvents => _domainEvents.AsReadOnly();
    protected void AddDomainEvent(INotification e) => _domainEvents.Add(e);
    public void ClearDomainEvents() => _domainEvents.Clear();
}
```

### Dispatching After SaveChanges

```csharp
using MediatR;
using Microsoft.EntityFrameworkCore;

public override async Task<int> SaveChangesAsync(CancellationToken ct = default)
{
    var entities = ChangeTracker.Entries()
        .Where(e => e.Entity is IHasDomainEvents)
        .Select(e => (IHasDomainEvents)e.Entity)
        .Where(e => e.DomainEvents.Any())
        .ToList();

    var events = entities.SelectMany(e => e.DomainEvents).ToList();
    entities.ForEach(e => e.ClearDomainEvents());

    var result = await base.SaveChangesAsync(ct);

    foreach (var domainEvent in events)
        await _publisher.Publish(domainEvent, ct);

    return result;
}
```

### Event Handler

```csharp
using MediatR;

public sealed class SendOrderConfirmationHandler(IEmailService emailService)
    : INotificationHandler<OrderSubmittedEvent>
{
    public async Task Handle(OrderSubmittedEvent notification, CancellationToken ct) =>
        await emailService.SendOrderConfirmationAsync(
            notification.CustomerId, notification.OrderId, ct);
}
```

---

## 5. Entity Base Classes

### Strongly-Typed IDs

Use `record struct` -- value types, stack-allocated, structural equality.

```csharp
public readonly record struct OrderId(Guid Value)
{
    public static OrderId New() => new(Guid.NewGuid());
    public override string ToString() => Value.ToString();
}

public readonly record struct CustomerId(Guid Value)
{
    public static CustomerId New() => new(Guid.NewGuid());
    public override string ToString() => Value.ToString();
}
```

### AuditableEntity

```csharp
using Microsoft.EntityFrameworkCore;

public abstract class AuditableEntity<TId> : Entity<TId> where TId : notnull
{
    public DateTimeOffset CreatedAt { get; set; }
    public DateTimeOffset? UpdatedAt { get; set; }
}

// In DbContext.SaveChangesAsync, before base.SaveChangesAsync:
foreach (var entry in ChangeTracker.Entries<AuditableEntity<object>>())
{
    if (entry.State == EntityState.Added) entry.Entity.CreatedAt = DateTimeOffset.UtcNow;
    if (entry.State == EntityState.Modified) entry.Entity.UpdatedAt = DateTimeOffset.UtcNow;
}
```

---

## 6. EF Core Mapping for DDD

Use `IEntityTypeConfiguration<T>`. No repository pattern -- `DbContext` is already Unit of Work + Repository.

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Metadata.Builders;

public sealed class OrderConfiguration : IEntityTypeConfiguration<Order>
{
    public void Configure(EntityTypeBuilder<Order> builder)
    {
        builder.HasKey(o => o.Id);
        builder.Property(o => o.Id).HasConversion(id => id.Value, v => new OrderId(v));
        builder.Property(o => o.CustomerId).HasConversion(id => id.Value, v => new CustomerId(v));
        builder.Ignore(o => o.DomainEvents);

        // Value object as owned type
        builder.OwnsOne(o => o.TotalAmount, money =>
        {
            money.Property(m => m.Amount).HasColumnName("TotalAmount").HasPrecision(18, 2);
            money.Property(m => m.Currency).HasColumnName("TotalCurrency").HasMaxLength(3);
        });

        // Private collection via backing field
        builder.Navigation(o => o.Items).HasField("_items");
        builder.OwnsMany(o => o.Items, item =>
        {
            item.WithOwner().HasForeignKey("OrderId");
            item.Property<int>("Id").ValueGeneratedOnAdd();
            item.HasKey("Id");
            item.Property(i => i.ProductId).HasConversion(id => id.Value, v => new ProductId(v));
            item.OwnsOne(i => i.UnitPrice, m =>
            {
                m.Property(x => x.Amount).HasColumnName("UnitPrice").HasPrecision(18, 2);
                m.Property(x => x.Currency).HasColumnName("UnitCurrency").HasMaxLength(3);
            });
        });
    }
}
```

---

## 7. Anti-Patterns to Avoid

| Anti-Pattern | Problem | Do This Instead |
|---|---|---|
| **Anemic model when logic exists** | Rules leak into services, duplicated validation | Put behavior on the entity |
| **Repository wrapping EF Core** | Unnecessary abstraction; DbContext is already UoW + Repo | Use DbContext directly |
| **Large aggregates** | Lock contention, slow hydration | Split smaller, reference by ID |
| **Events inside the transaction** | Side effects roll back or cause partial failures | Dispatch after SaveChanges via IHasDomainEvents |
| **Public setters on entities** | Any code can create invalid state | Private setters + behavior methods |
| **Primitive obsession** | CustomerIds confused with OrderIds | Strongly-typed IDs and value objects |
| **Logic in controllers/handlers** | Untestable, scattered rules | Push logic into the domain model |
| **Wrong-layer validation** | Input format mixed with domain invariants | API validates shape; domain enforces invariants |
