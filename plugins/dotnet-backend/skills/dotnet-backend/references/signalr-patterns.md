# SignalR Real-Time Communication Patterns - .NET 9

## Strongly-Typed Hub Design

Define a client interface to get compile-time safety on server-to-client calls. Organize hub methods by domain concern and inject services through constructor DI.

```csharp
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Logging;

// Contract for server-to-client messages
public interface INotificationClient
{
    Task ReceiveOrderUpdate(OrderStatusDto status);
    Task ReceiveMessage(ChatMessageDto message);
    Task UserJoined(string userId, string displayName);
    Task UserLeft(string userId);
}

// Strongly-typed hub with DI
public class NotificationHub : Hub<INotificationClient>
{
    private readonly IOrderService _orderService;
    private readonly ILogger<NotificationHub> _logger;

    public NotificationHub(IOrderService orderService, ILogger<NotificationHub> logger)
    {
        _orderService = orderService;
        _logger = logger;
    }

    public override async Task OnConnectedAsync()
    {
        var userId = Context.UserIdentifier;
        _logger.LogInformation("Client connected: {ConnectionId}, User: {UserId}",
            Context.ConnectionId, Context.UserIdentifier);
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogInformation("User {UserId} disconnected", Context.UserIdentifier);
        await base.OnDisconnectedAsync(exception);
    }

    // Hub methods — keep focused, delegate to services
    public async Task SendMessage(string groupName, string content)
    {
        var userId = Context.UserIdentifier ?? throw new HubException("Unauthenticated");
        var message = new ChatMessageDto(userId, content, DateTimeOffset.UtcNow);
        await Clients.Group(groupName).ReceiveMessage(message);
    }

    public async Task SubscribeToOrder(string orderId)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"order-{orderId}");
    }
}
```

Register the hub in `Program.cs`:

```csharp
builder.Services.AddSignalR()
    .AddMessagePackProtocol(); // optional binary protocol

app.MapHub<NotificationHub>("/hubs/notifications");
```

## Group Management

Groups are the primary mechanism for scoping real-time messages to relevant clients. Connections can belong to multiple groups simultaneously.

```csharp
// Add current connection to a group
await Groups.AddToGroupAsync(Context.ConnectionId, $"tenant-{tenantId}");

// Remove from group
await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"tenant-{tenantId}");

// Send to group from inside the hub
await Clients.Group($"tenant-{tenantId}").ReceiveOrderUpdate(status);

// Send to group excluding the caller
await Clients.GroupExcept($"tenant-{tenantId}", [Context.ConnectionId])
    .ReceiveMessage(message);

// Send to a specific user (all their connections)
await Clients.User(userId).ReceiveOrderUpdate(status);
```

Assign groups during connection based on claims:

```csharp
using System.Security.Claims;

public override async Task OnConnectedAsync()
{
    var tenantId = Context.User?.FindFirst("tenant_id")?.Value;
    if (tenantId is not null)
        await Groups.AddToGroupAsync(Context.ConnectionId, $"tenant-{tenantId}");

    var roles = Context.User?.FindAll(ClaimTypes.Role).Select(c => c.Value) ?? [];
    foreach (var role in roles)
        await Groups.AddToGroupAsync(Context.ConnectionId, $"role-{role}");

    await base.OnConnectedAsync();
}
```

## Authentication

WebSocket connections cannot send custom headers after the initial handshake, so JWT tokens are passed via the query string. Configure the authentication middleware to read from both the `Authorization` header and the `access_token` query parameter.

```csharp
using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.IdentityModel.Tokens;

builder.Services.AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = builder.Configuration["Jwt:Issuer"],
            ValidateAudience = true,
            ValidAudience = builder.Configuration["Jwt:Audience"],
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(
                Encoding.UTF8.GetBytes(builder.Configuration["Jwt:Key"]!))
        };

        // SignalR sends the token on the query string for WebSocket
        options.Events = new JwtBearerEvents
        {
            OnMessageReceived = context =>
            {
                var accessToken = context.Request.Query["access_token"];
                var path = context.HttpContext.Request.Path;
                if (!string.IsNullOrEmpty(accessToken) && path.StartsWithSegments("/hubs"))
                {
                    context.Token = accessToken;
                }
                return Task.CompletedTask;
            }
        };
    });

app.UseAuthentication();
app.UseAuthorization();

app.MapHub<NotificationHub>("/hubs/notifications").RequireAuthorization();
```

Access the authenticated user inside the hub:

```csharp
public async Task SendMessage(string groupName, string content)
{
    var userId = Context.UserIdentifier; // populated from ClaimTypes.NameIdentifier
    var tenantId = Context.User?.FindFirst("tenant_id")?.Value;
    // ...
}
```

## Integration with MediatR

Use `IHubContext<THub, TClient>` to push SignalR notifications from MediatR handlers. This keeps the hub thin and lets domain events drive real-time updates.

```csharp
using MediatR;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Logging;

// Domain event
public record OrderStatusChangedEvent(string OrderId, string Status, string TenantId) : INotification;

// MediatR handler that pushes to SignalR
public class OrderStatusChangedHandler : INotificationHandler<OrderStatusChangedEvent>
{
    private readonly IHubContext<NotificationHub, INotificationClient> _hubContext;
    private readonly ILogger<OrderStatusChangedHandler> _logger;

    public OrderStatusChangedHandler(
        IHubContext<NotificationHub, INotificationClient> hubContext,
        ILogger<OrderStatusChangedHandler> logger)
    {
        _hubContext = hubContext;
        _logger = logger;
    }

    public async Task Handle(OrderStatusChangedEvent notification, CancellationToken ct)
    {
        _logger.LogInformation("Broadcasting order {OrderId} status: {Status}",
            notification.OrderId, notification.Status);

        var dto = new OrderStatusDto(notification.OrderId, notification.Status);

        // Notify the order-specific group
        await _hubContext.Clients
            .Group($"order-{notification.OrderId}")
            .ReceiveOrderUpdate(dto);

        // Notify the tenant group
        await _hubContext.Clients
            .Group($"tenant-{notification.TenantId}")
            .ReceiveOrderUpdate(dto);
    }
}
```

Publish the event from your application service or command handler:

```csharp
await _mediator.Publish(new OrderStatusChangedEvent(order.Id, "Shipped", order.TenantId), ct);
```

## Client Patterns

### JavaScript/TypeScript Connection Management

```typescript
import { HubConnectionBuilder, HubConnectionState, LogLevel } from "@microsoft/signalr";
import { MessagePackHubProtocol } from "@microsoft/signalr-protocol-msgpack";

const connection = new HubConnectionBuilder()
  .withUrl("/hubs/notifications", {
    accessTokenFactory: () => getAccessToken(),
  })
  .withHubProtocol(new MessagePackHubProtocol()) // binary, smaller payloads
  .withAutomaticReconnect([0, 2000, 5000, 10000, 30000]) // custom retry delays
  .configureLogging(LogLevel.Information)
  .build();

connection.onreconnecting((error) => {
  console.warn("Connection lost. Reconnecting...", error);
  showReconnectingBanner();
});

connection.onreconnected((connectionId) => {
  console.info("Reconnected:", connectionId);
  hideReconnectingBanner();
  resubscribeToGroups(); // re-join groups after reconnect
});

connection.onclose((error) => {
  console.error("Connection closed permanently:", error);
  showDisconnectedState();
});

// Register handlers before starting
connection.on("ReceiveOrderUpdate", (status) => updateOrderUI(status));
connection.on("ReceiveMessage", (message) => appendMessage(message));

async function start() {
  if (connection.state === HubConnectionState.Disconnected) {
    await connection.start();
  }
}

start();
```

### MessagePack Protocol

MessagePack produces smaller payloads and faster serialization than JSON. Enable it on both server and client.

Server: `builder.Services.AddSignalR().AddMessagePackProtocol();`
Client: pass `new MessagePackHubProtocol()` to `.withHubProtocol()` as shown above.

## Scaling with Redis Backplane

A single SignalR server keeps group and connection state in memory. When scaling to multiple instances, use the Redis backplane so messages reach all connected clients regardless of which server they are connected to.

```csharp
using StackExchange.Redis;

builder.Services.AddSignalR()
    .AddStackExchangeRedis(builder.Configuration.GetConnectionString("Redis")!, options =>
    {
        options.Configuration.ChannelPrefix = RedisChannel.Literal("NotificationHub");
    });
```

Sticky sessions (affinity) are required for transports that use multiple HTTP requests (Long Polling, Server-Sent Events). WebSocket connections are persistent and do not strictly need affinity, but enabling it avoids issues during transport negotiation.

Configure in your load balancer or Kubernetes ingress:

```yaml
# NGINX Ingress annotation for sticky sessions
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "SignalRAffinity"
    nginx.ingress.kubernetes.io/session-cookie-hash: "sha1"
```

## Testing SignalR

### Integration Testing Hubs

Use `WebApplicationFactory` and the SignalR client to write end-to-end hub tests.

```csharp
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.AspNetCore.SignalR.Client;

public class NotificationHubTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public NotificationHubTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory;
    }

    [Fact]
    public async Task SendMessage_BroadcastsToGroup()
    {
        var server = _factory.WithWebHostBuilder(b => { /* test overrides */ });
        var client = server.CreateClient();

        var connection = new HubConnectionBuilder()
            .WithUrl($"{client.BaseAddress}hubs/notifications", options =>
            {
                options.HttpMessageHandlerFactory = _ => server.Server.CreateHandler();
            })
            .Build();

        var received = new TaskCompletionSource<ChatMessageDto>();
        connection.On<ChatMessageDto>("ReceiveMessage", msg => received.SetResult(msg));

        await connection.StartAsync();
        await connection.InvokeAsync("SubscribeToOrder", "order-123");
        await connection.InvokeAsync("SendMessage", "order-123", "Hello");

        var message = await received.Task.WaitAsync(TimeSpan.FromSeconds(5));
        Assert.Equal("Hello", message.Content);

        await connection.StopAsync();
    }
}
```

### Mocking IHubContext in Unit Tests

When testing MediatR handlers or services that send SignalR messages, mock the hub context using NSubstitute.

```csharp
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Logging;
using NSubstitute;

[Fact]
public async Task Handle_SendsNotificationToOrderGroup()
{
    var mockClients = Substitute.For<IHubClients<INotificationClient>>();
    var mockClient = Substitute.For<INotificationClient>();
    mockClients.Group(Arg.Any<string>()).Returns(mockClient);

    var hubContext = Substitute.For<IHubContext<NotificationHub, INotificationClient>>();
    hubContext.Clients.Returns(mockClients);

    var logger = Substitute.For<ILogger<OrderStatusChangedHandler>>();

    var handler = new OrderStatusChangedHandler(hubContext, logger);

    var evt = new OrderStatusChangedEvent("order-1", "Shipped", "tenant-abc");
    await handler.Handle(evt, CancellationToken.None);

    await mockClient.Received(1).ReceiveOrderUpdate(Arg.Is<OrderStatusDto>(
        d => d.OrderId == "order-1" && d.Status == "Shipped"));
}
```
