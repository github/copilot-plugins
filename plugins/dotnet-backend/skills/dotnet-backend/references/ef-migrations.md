# EF Core 9 Migration Best Practices (.NET 9)

## 1. Migration Basics

### Core Commands

```bash
# Create new migration
dotnet ef migrations add <MigrationName> --project <ProjectPath>

# Remove last migration (if not applied)
dotnet ef migrations remove --project <ProjectPath>

# Apply migrations to database
dotnet ef database update --project <ProjectPath>

# Rollback to specific migration
dotnet ef database update <MigrationName> --project <ProjectPath>

# Generate SQL script
dotnet ef migrations script --project <ProjectPath> --output migration.sql

# List all migrations
dotnet ef migrations list --project <ProjectPath>
```

### Naming Conventions

```bash
# Good: Descriptive, action-oriented
dotnet ef migrations add AddUserEmailIndex
dotnet ef migrations add CreateProductsTable
dotnet ef migrations add UpdateOrderStatusEnum

# Bad: Generic, unclear
dotnet ef migrations add Update1
dotnet ef migrations add Changes
```

### When to Create New vs Modify Existing

**Create new migration when:**
- Migration already applied to any environment (dev, staging, prod)
- Migration exists in shared branch (main, develop)
- Migration pushed to remote repository

**Modify existing migration when:**
- Only in local development
- Not yet applied to any database
- Not shared with team

```bash
# Safe to modify: remove and recreate
dotnet ef migrations remove
# Make model changes
dotnet ef migrations add AddUserEmailIndex
```

## 2. Team Workflow

### Handling Merge Conflicts

**ModelSnapshot conflicts are common:**

```bash
# After pulling/merging, regenerate snapshot
dotnet ef migrations remove  # Remove your local migration
git pull origin main
dotnet ef migrations add YourMigrationName  # Recreate with updated snapshot
```

**Multiple developers creating migrations simultaneously:**

```bash
# Developer A: 20240206120000_AddUserEmail.cs
# Developer B: 20240206120100_AddProductSku.cs

# After merge, verify order
dotnet ef migrations list

# If order is wrong, recreate migrations in correct sequence
```

### One Migration Per PR Rule

```bash
# Good: Single focused migration
- PR #123: AddUserEmailIndex
  - 20240206_AddUserEmailIndex.cs
  - Updated ModelSnapshot

# Bad: Multiple migrations
- PR #124: Multiple changes
  - 20240206_AddUserEmail.cs
  - 20240207_AddProductSku.cs
  - 20240208_UpdateOrders.cs
```

### Migration Ordering in Branches

```csharp
// Feature branch workflow
// 1. Create feature branch from main
git checkout -b feature/add-user-email

// 2. Make model changes
public class User
{
    public string Email { get; set; } = string.Empty;
}

// 3. Create migration
dotnet ef migrations add AddUserEmail

// 4. Before PR, rebase on latest main
git fetch origin
git rebase origin/main

// 5. If conflicts, regenerate migration
dotnet ef migrations remove
dotnet ef migrations add AddUserEmail
```

## 3. CI/CD Integration

### Migration Bundles (Recommended for .NET 9)

```bash
# Create migration bundle (self-contained executable)
dotnet ef migrations bundle --project MyApp.Infrastructure --output efbundle

# Run in deployment pipeline
./efbundle --connection "Server=prod;Database=mydb;..."
```

### Idempotent SQL Scripts

```bash
# Generate idempotent script (safe to run multiple times)
dotnet ef migrations script --idempotent --output migrations.sql --project MyApp.Infrastructure

# Apply in CI/CD
sqlcmd -S server -d database -i migrations.sql
```

### Bundles vs Scripts Comparison

| Feature | Migration Bundles | SQL Scripts |
|---------|------------------|-------------|
| Cross-platform | Yes | Database-specific |
| Runtime deps | .NET Runtime | Database client |
| Rollback | Built-in | Manual |
| Azure DevOps | Easy | Requires SQL task |
| Docker | Single file | Requires tooling |

### Deployment Pipeline Example

```yaml
# Azure DevOps pipeline
- task: DotNetCoreCLI@2
  displayName: 'Create EF Bundle'
  inputs:
    command: 'custom'
    custom: 'ef'
    arguments: 'migrations bundle --configuration Release --output $(Build.ArtifactStagingDirectory)/efbundle'

- task: Bash@3
  displayName: 'Apply Migrations'
  inputs:
    targetType: 'inline'
    script: |
      chmod +x $(Pipeline.Workspace)/drop/efbundle
      $(Pipeline.Workspace)/drop/efbundle --connection "$(ConnectionString)"
```

**Never run migrations in application startup:**

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

// WRONG: Don't do this in production
public static void Main(string[] args)
{
    var host = CreateHostBuilder(args).Build();

    using (var scope = host.Services.CreateScope())
    {
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        db.Database.Migrate(); // DANGEROUS in production
    }

    host.Run();
}

// RIGHT: Run migrations in deployment pipeline
// Application startup should only verify migrations are current
```

## 4. Data Seeding

### HasData for Static Reference Data

```csharp
using Microsoft.EntityFrameworkCore;

public class AppDbContext : DbContext
{
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<OrderStatus>().HasData(
            new OrderStatus { Id = 1, Name = "Pending" },
            new OrderStatus { Id = 2, Name = "Processing" },
            new OrderStatus { Id = 3, Name = "Completed" }
        );
    }
}
```

### Custom Data Seeding Migrations

```csharp
using Microsoft.EntityFrameworkCore.Migrations;

// Create empty migration for data seeding
// dotnet ef migrations add SeedUserRoles

// Edit migration manually
public partial class SeedUserRoles : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.Sql(@"
            INSERT INTO Roles (Id, Name) VALUES
            ('admin-guid', 'Administrator'),
            ('user-guid', 'User');
        ");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.Sql(@"
            DELETE FROM Roles WHERE Id IN ('admin-guid', 'user-guid');
        ");
    }
}
```

### Environment-Specific Seeds

```csharp
using Microsoft.AspNetCore.Hosting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Hosting;

public static class DatabaseSeeder
{
    public static async Task SeedAsync(AppDbContext context, IWebHostEnvironment env)
    {
        if (env.IsDevelopment())
        {
            await SeedTestDataAsync(context);
        }

        // Always seed reference data
        await SeedReferenceDataAsync(context);
    }

    private static async Task SeedTestDataAsync(AppDbContext context)
    {
        if (!await context.Users.AnyAsync())
        {
            context.Users.AddRange(
                new User { Email = "test1@example.com" },
                new User { Email = "test2@example.com" }
            );
            await context.SaveChangesAsync();
        }
    }
}
```

## 5. Advanced Patterns

### Data Migrations (Transform Existing Data)

```csharp
using Microsoft.EntityFrameworkCore.Migrations;

// dotnet ef migrations add MigrateUserEmailToLowercase

public partial class MigrateUserEmailToLowercase : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        // Step 1: Add new column
        migrationBuilder.AddColumn<string>(
            name: "EmailNormalized",
            table: "Users",
            nullable: true);

        // Step 2: Migrate data
        migrationBuilder.Sql(@"
            UPDATE Users
            SET EmailNormalized = LOWER(Email)
        ");

        // Step 3: Make non-nullable
        migrationBuilder.AlterColumn<string>(
            name: "EmailNormalized",
            table: "Users",
            nullable: false);
    }
}
```

### Custom SQL for Performance

```csharp
using Microsoft.EntityFrameworkCore.Migrations;

public partial class AddUserEmailIndex : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        // PostgreSQL: CREATE INDEX CONCURRENTLY (non-blocking)
        // SQL Server: CREATE INDEX ... WITH (ONLINE = ON) (Enterprise edition)
        migrationBuilder.Sql(
            ActiveProvider == "Npgsql.EntityFrameworkCore.PostgreSQL"
                ? "CREATE INDEX CONCURRENTLY IX_Users_Email ON \"Users\" (\"Email\")"
                : "CREATE NONCLUSTERED INDEX IX_Users_Email ON Users (Email)");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropIndex("IX_Users_Email", "Users");
    }
}
```

### Expand-Contract Pattern for Breaking Changes

```csharp
using Microsoft.EntityFrameworkCore.Migrations;

// Phase 1: Expand - Add new column
// dotnet ef migrations add AddUserFullName

public partial class AddUserFullName : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.AddColumn<string>("FullName", "Users", nullable: true);

        // Populate from existing data
        migrationBuilder.Sql(@"
            UPDATE Users
            SET FullName = CONCAT(FirstName, ' ', LastName)
        ");
    }
}

// Deploy application that writes to both old and new columns
// Wait for deployment...

// Phase 2: Contract - Remove old columns
// dotnet ef migrations add RemoveUserNameColumns

public partial class RemoveUserNameColumns : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.DropColumn("FirstName", "Users");
        migrationBuilder.DropColumn("LastName", "Users");

        migrationBuilder.AlterColumn<string>(
            "FullName", "Users", nullable: false);
    }
}
```

### Column Renames Without Data Loss

```csharp
using Microsoft.EntityFrameworkCore.Migrations;

public partial class RenameUserEmailColumn : Migration
{
    protected override void Up(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.RenameColumn(
            name: "Email",
            table: "Users",
            newName: "EmailAddress");
    }

    protected override void Down(MigrationBuilder migrationBuilder)
    {
        migrationBuilder.RenameColumn(
            name: "EmailAddress",
            table: "Users",
            newName: "Email");
    }
}
```

## 6. Modular Monolith Considerations

### Per-Module DbContext Setup

```csharp
using Microsoft.EntityFrameworkCore;

// Orders module
public class OrdersDbContext : DbContext
{
    public OrdersDbContext(DbContextOptions<OrdersDbContext> options)
        : base(options) { }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasDefaultSchema("orders");
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(OrdersDbContext).Assembly);
    }
}

// Products module
public class ProductsDbContext : DbContext
{
    public ProductsDbContext(DbContextOptions<ProductsDbContext> options)
        : base(options) { }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.HasDefaultSchema("products");
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(ProductsDbContext).Assembly);
    }
}
```

### Independent Migration Histories

```bash
# Create migrations per module
dotnet ef migrations add InitialCreate --context OrdersDbContext --project Orders.Infrastructure
dotnet ef migrations add InitialCreate --context ProductsDbContext --project Products.Infrastructure

# Apply migrations independently
dotnet ef database update --context OrdersDbContext --project Orders.Infrastructure
dotnet ef database update --context ProductsDbContext --project Products.Infrastructure

# Generate separate bundles
dotnet ef migrations bundle --context OrdersDbContext --output orders-bundle
dotnet ef migrations bundle --context ProductsDbContext --output products-bundle
```

### Schema Separation Benefits

```csharp
// Tables are isolated by schema
// orders.Orders, orders.OrderItems
// products.Products, products.Categories

// Migration history tables are separate
// orders.__EFMigrationsHistory
// products.__EFMigrationsHistory
```

## 7. Common Pitfalls

### Startup Migrations (Don't Do This)

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

// WRONG: Multiple app instances = race conditions, locks, failures
public static void Main(string[] args)
{
    var host = CreateHostBuilder(args).Build();
    using (var scope = host.Services.CreateScope())
    {
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        db.Database.Migrate(); // Bad in production
    }
    host.Run();
}

// RIGHT: Use deployment pipeline with migration bundles
// App only reads data, never modifies schema
```

### Table Locking During Migrations

```csharp
using Microsoft.EntityFrameworkCore.Migrations;

// WRONG: Locks entire table in production
migrationBuilder.AddColumn<string>("Email", "Users", nullable: false);

// RIGHT: Multi-phase approach
// Phase 1: Add nullable column
migrationBuilder.AddColumn<string>("Email", "Users", nullable: true);

// Phase 2: Backfill data (separate deployment)
migrationBuilder.Sql("UPDATE Users SET Email = LegacyEmail WHERE Email IS NULL");

// Phase 3: Make non-nullable (separate deployment)
migrationBuilder.AlterColumn<string>("Email", "Users", nullable: false);
```

### Null to Non-Null Transitions

```csharp
using Microsoft.EntityFrameworkCore.Migrations;

// WRONG: Will fail if existing rows have NULL
migrationBuilder.AlterColumn<string>(
    "Email", "Users", nullable: false, oldNullable: true);

// RIGHT: Three-step process
// Migration 1: Add column as nullable
migrationBuilder.AddColumn<string>("Email", "Users", nullable: true);

// Migration 2: Populate data
migrationBuilder.Sql("UPDATE Users SET Email = 'default@example.com' WHERE Email IS NULL");

// Migration 3: Make non-nullable
migrationBuilder.AlterColumn<string>("Email", "Users", nullable: false);
```

### EnsureCreated vs Migrate

```csharp
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

// WRONG: EnsureCreated bypasses migrations entirely
context.Database.EnsureCreated(); // Creates schema without migration history

// WRONG: Mixing both
context.Database.EnsureCreated(); // Creates tables
context.Database.Migrate(); // Fails - tables already exist

// RIGHT: Use Migrate for all environments
context.Database.Migrate(); // Respects migration history

// RIGHT: Or for testing, use in-memory database
services.AddDbContext<AppDbContext>(options =>
    options.UseInMemoryDatabase("TestDb"));
```

### Managing Connection Strings

```bash
# Development: User secrets
dotnet user-secrets init
dotnet user-secrets set "ConnectionStrings:Default" "Server=localhost;..."

# CI/CD: Environment variables or Azure Key Vault
export ConnectionStrings__Default="Server=prod;..."

# Bundle with connection string override
./efbundle --connection "$(CONNECTION_STRING)"
```

## Summary Checklist

- Use migration bundles for deployment automation
- One migration per PR to avoid conflicts
- Never run migrations in application startup
- Use expand-contract for breaking changes
- Separate schemas for modular monoliths
- Test migrations on production-like data volumes
- Generate idempotent scripts for SQL-based deployments
- Always provide Down methods for rollback capability
- Use HasData only for static reference data
- Custom SQL for data transformations and performance-critical operations
