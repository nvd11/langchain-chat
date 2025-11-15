# 数据库设计文档

本文档详细描述了聊天应用后端所使用的 PostgreSQL 数据库的表结构，严格遵循 `Requirement.zh-CN.md` 中定义的核心需求。

---

## 1. 核心设计理念

- **异步支持**: 所有表的设计都与 SQLAlchemy 的异步 ORM 兼容。
- **UUID 主键**: 使用 `UUID` 作为主键 (`id`)，以避免在分布式系统中出现ID冲突，并隐藏实际的行数。
- **时间戳**: 所有表都包含一个 `created_at` 字段，并由数据库服务器自动填充，以记录创建时间。
- **关系**: 表之间通过外键建立清晰的关系，并定义了级联删除等行为。

---

## 2. 表结构详情

### 2.1. `conversations` 表

该表存储每一个独立的对话会话。

| 字段名      | 数据类型                 | 约束/默认值        | 描述                               |
|-------------|--------------------------|--------------------|------------------------------------|
| `id`        | `UUID`                   | **主键**, `uuid.uuid4` | 对话的唯一标识符。                 |
| `created_at`| `DateTime(timezone=True)`| `server_default=func.now()` | 对话的创建时间（带时区）。         |

**关系**:
- 与 `messages` 表是一对多关系。当一个对话被删除时，所有关联的消息也会被级联删除 (`cascade="all, delete-orphan"`)。

---

### 2.2. `messages` 表

该表存储在一次对话中，用户与助手之间的每一条消息。

| 字段名            | 数据类型                 | 约束/默认值        | 描述                               |
|-------------------|--------------------------|--------------------|------------------------------------|
| `id`              | `UUID`                   | **主键**, `uuid.uuid4` | 消息的唯一标识符。                 |
| `conversation_id` | `UUID`                   | **外键** (conversations.id) | 关联的对话ID。                     |
| `role`            | `String`                 | `nullable=False`   | 消息发送者的角色 (`user` 或 `assistant`)。 |
| `content`         | `Text`                   | `nullable=False`   | 消息的具体文本内容。               |
| `created_at`      | `DateTime(timezone=True)`| `server_default=func.now()` | 消息的创建时间（带时区）。         |

**关系**:
- 与 `conversations` 表是多对一关系。
