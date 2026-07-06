from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionName(str, Enum):
    NOOP = "NOOP"
    SCALE_OUT = "SCALE_OUT"
    SCALE_IN = "SCALE_IN"
    THROTTLE_LOW_PRIORITY = "THROTTLE_LOW_PRIORITY"
    REJECT_LOW_PRIORITY = "REJECT_LOW_PRIORITY"
    ENABLE_LONG_CONTEXT_QUEUE = "ENABLE_LONG_CONTEXT_QUEUE"
    WARN_GPU_MEMORY_PRESSURE = "WARN_GPU_MEMORY_PRESSURE"
    WARN_P99_VIOLATION = "WARN_P99_VIOLATION"
    WARN_HPA_LAG = "WARN_HPA_LAG"


@dataclass(slots=True)//slots是dataclass的扩展项 内存更省访问更快大量短周期对象或高并发场景
class RequestMetrics:
    request_id: str
    tenant_id: str
    workload_type: str
    prompt_tokens: int
    output_tokens: int
    start_time: float
    first_token_time: float | None
    end_time: float
    status_code: int
    error_reason: str = ""
    retry_count: int = 0
    streaming: bool = True

    @property
    def ttft(self) -> float | None:
        if self.first_token_time is None:
            return None
        return max(0.0, self.first_token_time - self.start_time)

    @property
    def latency(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    @property
    def tpot(self) -> float | None:
        if self.first_token_time is None or self.output_tokens <= 1:
            return None
        return max(0.0, (self.end_time - self.first_token_time) / (self.output_tokens - 1))

    def as_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "workload_type": self.workload_type,
            "prompt_tokens": self.prompt_tokens,
            "output_tokens": self.output_tokens,
            "start_time": self.start_time,
            "first_token_time": self.first_token_time,
            "end_time": self.end_time,
            "ttft": self.ttft,
            "tpot": self.tpot,
            "latency": self.latency,
            "status_code": self.status_code,
            "error_reason": self.error_reason,
            "retry_count": self.retry_count,
            "streaming": self.streaming,
        }


@dataclass(slots=True)
class ControllerMetrics:
    queue_time_p95: float = 0.0//
    queue_time_p99: float = 0.0
    ttft_p95: float = 0.0
    ttft_p99: float = 0.0
    tpot_p95: float = 0.0
    tpot_p99: float = 0.0
    e2e_latency_p99: float = 0.0
    waiting_requests: float = 0.0
    running_requests: float = 0.0
    gpu_memory_ratio: float = 0.0
    gpu_utilization: float = 0.0
    prompt_tokens_per_sec: float = 0.0
    generation_tokens_per_sec: float = 0.0
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    current_replicas: int = 1
    long_context_ratio: float = 0.0
    tenant_overload_ratio: float = 0.0
    missing: list[str] = field(default_factory=list)//可变默认值


@dataclass(slots=True)
class Decision:
    action: ActionName
    reason: str
    desired_replicas: int | None = None
    severity: str = "info"
    signals: dict[str, float | int | str] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.value,
            "reason": self.reason,
            "desired_replicas": self.desired_replicas,
            "severity": self.severity,
            "signals": self.signals,
        }
       
        
        










"""# Python 语法笔记：类型标注、数据类、枚举、对象、属性方法

## 1. 类型标注

类型标注是 Python 中用来说明变量、参数、返回值“应该是什么类型”的语法。

例如：

```python
request_id: str
prompt_tokens: int
start_time: float
streaming: bool
first_token_time: float | None
missing: list[str]
signals: dict[str, float | int | str]
```

含义如下：

```python
request_id: str
```

表示 `request_id` 应该是字符串。

```python
prompt_tokens: int
```

表示 `prompt_tokens` 应该是整数。

```python
start_time: float
```

表示 `start_time` 应该是浮点数，也就是小数。

```python
streaming: bool
```

表示 `streaming` 应该是布尔值，只能是 `True` 或 `False`。

```python
first_token_time: float | None
```

表示 `first_token_time` 要么是 `float`，要么是 `None`。

这里的 `|` 可以理解为“或者”。

所以：

```python
float | None
```

就是：

```text
float 或 None
```

```python
missing: list[str]
```

表示 `missing` 是一个列表，并且列表里的元素都是字符串。

例如：

```python
missing = ["ttft_p99", "gpu_memory_ratio"]
```

```python
signals: dict[str, float | int | str]
```

表示 `signals` 是一个字典，key 是字符串，value 可以是浮点数、整数或字符串。

例如：

```python
signals = {
    "ttft_p99": 3.5,
    "current_replicas": 2,
    "policy": "scale_out_on_p99",
}
```

需要注意：Python 默认不会强制检查类型标注。类型标注主要是给人、编辑器、类型检查工具看的，可以提升代码可读性和可维护性。

---

## 2. 什么是类

类是模板，用来定义一类对象应该有哪些数据和方法。

例如：

```python
@dataclass
class RequestMetrics:
    request_id: str
    tenant_id: str
    prompt_tokens: int
    output_tokens: int
```

这里的 `RequestMetrics` 是一个类。

它规定了一个请求指标对象应该有：

```text
request_id
tenant_id
prompt_tokens
output_tokens
```

但是这里只是定义模板，还没有真正创建具体数据。

---

## 3. 什么是对象

对象是根据类创建出来的具体实例。

例如：

```python
m = RequestMetrics(
    request_id="req-001",
    tenant_id="tenant-a",
    prompt_tokens=100,
    output_tokens=20,
)
```

这里的 `m` 就是一个对象。

也可以说：

```text
m 是 RequestMetrics 类的一个实例
```

对象和实例在这里基本可以当成一个意思。

类和对象的关系可以理解为：

```text
类：表格模板
对象：填好的一行具体数据
```

例如：

```python
m1 = RequestMetrics("req-001", "tenant-a", 100, 20)
m2 = RequestMetrics("req-002", "tenant-b", 300, 80)
```

`m1` 和 `m2` 都是 `RequestMetrics` 类创建出来的对象，但它们里面的数据不同。

---

## 4. 实例化

实例化就是用类创建对象的过程。

例如：

```python
m = RequestMetrics(...)
```

这就是实例化。

可以理解为：

```text
用 RequestMetrics 这个模板，创建了一个具体的 RequestMetrics 对象 m
```

只要是通过：

```python
变量名 = 类名(...)
```

创建出来的具体变量，通常就是一个对象。

---

## 5. 对象里的属性和方法

一个对象通常有两类东西：

```text
属性：对象里存的数据
方法：对象能执行的函数
```

例如：

```python
decision = Decision(
    action=ActionName.SCALE_OUT,
    reason="ttft_p99 too high",
)
```

这里的 `decision` 是对象。

它的属性有：

```python
decision.action
decision.reason
decision.desired_replicas
decision.severity
decision.signals
```

它的方法有：

```python
decision.as_dict()
```

属性是数据，方法是函数逻辑。

---

## 6. 什么是数据类

数据类是主要用来存数据的类。

普通类如果要存数据，通常需要手写 `__init__`：

```python
class RequestMetrics:
    def __init__(self, request_id, tenant_id, prompt_tokens):
        self.request_id = request_id
        self.tenant_id = tenant_id
        self.prompt_tokens = prompt_tokens
```

用了 `@dataclass` 后，可以简化成：

```python
@dataclass
class RequestMetrics:
    request_id: str
    tenant_id: str
    prompt_tokens: int
```

Python 会自动帮你生成初始化函数。

所以你可以直接创建对象：

```python
m = RequestMetrics(
    request_id="req-001",
    tenant_id="tenant-a",
    prompt_tokens=100,
)
```

数据类适合用来表达一组结构化数据。

例如：

```python
@dataclass
class ControllerMetrics:
    ttft_p99: float = 0.0
    gpu_memory_ratio: float = 0.0
    current_replicas: int = 1
```

这个类的作用就是存放控制器当前看到的系统指标。

---

## 7. 必填字段和默认字段

在数据类里，字段分为两类。

第一类是没有默认值的字段：

```python
request_id: str
tenant_id: str
prompt_tokens: int
start_time: float
end_time: float
```

这些字段在创建对象时必须传。

例如：

```python
m = RequestMetrics(
    request_id="req-001",
    tenant_id="tenant-a",
    prompt_tokens=100,
    start_time=10.0,
    end_time=12.0,
)
```

第二类是有默认值的字段：

```python
error_reason: str = ""
retry_count: int = 0
streaming: bool = True
```

这些字段可以不传。

如果不传，Python 会使用默认值。

例如：

```python
m = RequestMetrics(
    request_id="req-001",
    tenant_id="tenant-a",
    prompt_tokens=100,
    start_time=10.0,
    end_time=12.0,
)
```

此时自动等价于：

```python
error_reason = ""
retry_count = 0
streaming = True
```

有默认值的字段也可以传。如果传了，就会覆盖默认值。

例如：

```python
m = RequestMetrics(
    request_id="req-001",
    tenant_id="tenant-a",
    prompt_tokens=100,
    start_time=10.0,
    end_time=12.0,
    retry_count=2,
    streaming=False,
)
```

总结：

```text
没有默认值：必须传
有默认值：可以不传；传了就覆盖默认值
```

---

## 8. 为什么有的字段默认是 `0.0`

例如：

```python
queue_time_p95: float = 0.0
ttft_p99: float = 0.0
gpu_memory_ratio: float = 0.0
error_rate: float = 0.0
```

这些是监控指标。

在系统刚启动、还没有采集到数据，或者某些指标暂时缺失时，可以先用 `0.0` 作为默认值。

例如：

```python
metrics = ControllerMetrics()
```

即使什么参数都不传，也能创建一个默认指标对象。

---

## 9. 可变对象和不可变对象

Python 中对象可以分为可变对象和不可变对象。

不可变对象是创建之后不能原地修改内容的对象。

常见不可变对象有：

```text
int
float
str
bool
None
tuple
```

例如：

```python
x = 1
x = x + 1
```

看起来 `x` 从 `1` 变成了 `2`，但本质上不是把整数 `1` 原地改成 `2`，而是让 `x` 指向了一个新的整数对象 `2`。

字符串也是不可变对象：

```python
s = "abc"
s = s + "d"
```

这不是把原来的 `"abc"` 原地修改，而是创建了新的字符串 `"abcd"`。

所以这些类型可以直接写默认值：

```python
retry_count: int = 0
severity: str = "info"
streaming: bool = True
gpu_memory_ratio: float = 0.0
desired_replicas: int | None = None
```

可变对象是创建之后可以原地修改内容的对象。

常见可变对象有：

```text
list
dict
set
```

例如列表：

```python
xs = []
xs.append("ttft_p99")
```

这里是直接修改原来的列表。

字典也是：

```python
d = {}
d["ttft_p99"] = 3.5
```

这里是直接修改原来的字典。

---

## 10. 为什么 `list` 和 `dict` 要用 `field(default_factory=...)`

错误写法：

```python
missing: list[str] = []
signals: dict[str, float | int | str] = {}
```

这种写法有风险，因为列表和字典是可变对象。如果直接作为默认值，多个对象可能共享同一个默认列表或字典。

例如：

```python
a = ControllerMetrics()
b = ControllerMetrics()

a.missing.append("ttft_p99")
```

如果 `missing` 的默认值直接写成 `[]`，可能导致 `b.missing` 也受到影响。

正确写法是：

```python
missing: list[str] = field(default_factory=list)
signals: dict[str, float | int | str] = field(default_factory=dict)
```

意思是：

```text
每次创建新对象时，都重新创建一个新的空列表或空字典
```

所以：

```python
field(default_factory=list)
```

等价于：

```text
每个对象单独有自己的 []
```

```python
field(default_factory=dict)
```

等价于：

```text
每个对象单独有自己的 {}
```

总结：

```text
int / float / str / bool / None：不可变，可以直接写默认值
list / dict / set：可变，要用 field(default_factory=...)
```

---

## 11. 什么是枚举

枚举是固定选项集合。

例如：

```python
class ActionName(str, Enum):
    NOOP = "NOOP"
    SCALE_OUT = "SCALE_OUT"
    SCALE_IN = "SCALE_IN"
    WARN_GPU_MEMORY_PRESSURE = "WARN_GPU_MEMORY_PRESSURE"
```

这里的 `ActionName` 是一个枚举类。

它规定动作只能从这些选项里选：

```python
ActionName.NOOP
ActionName.SCALE_OUT
ActionName.SCALE_IN
ActionName.WARN_GPU_MEMORY_PRESSURE
```

枚举的作用是防止字符串乱写。

如果不用枚举，可能会写：

```python
action = "SCALE_OUT"
```

但也可能手滑写错：

```python
action = "SCAL_OUT"
```

少写了一个 `E`，Python 不会提前知道这是错的。

用枚举后：

```python
action = ActionName.SCALE_OUT
```

如果写成：

```python
ActionName.SCAL_OUT
```

会直接报错，因为枚举里没有这个选项。

---

## 12. `class ActionName(str, Enum):` 里的 `str` 和 `Enum`

```python
class ActionName(str, Enum):
```

括号里的 `str` 和 `Enum` 表示继承。

可以理解为：

```text
ActionName 既是枚举，又像字符串
```

其中：

```python
Enum
```

表示这是一个枚举类。

```python
str
```

表示枚举的值底层是字符串。

例如：

```python
ActionName.SCALE_OUT
```

是枚举成员。

它背后的字符串值是：

```python
ActionName.SCALE_OUT.value
```

结果是：

```python
"SCALE_OUT"
```

内部程序里推荐用：

```python
ActionName.SCALE_OUT
```

输出到日志、接口、JSON 时通常用：

```python
ActionName.SCALE_OUT.value
```

得到普通字符串：

```python
"SCALE_OUT"
```

---

## 13. `self` 是什么

`self` 表示当前对象自己。

例如：

```python
@dataclass
class Decision:
    action: ActionName
    reason: str

    def as_dict(self):
        return {
            "action": self.action.value,
            "reason": self.reason,
        }
```

如果创建对象：

```python
decision = Decision(
    action=ActionName.SCALE_OUT,
    reason="ttft_p99 too high",
)
```

然后调用：

```python
decision.as_dict()
```

Python 会自动把 `decision` 这个对象传给 `self`。

所以方法内部：

```python
self.action
```

就是：

```python
decision.action
```

```python
self.reason
```

就是：

```python
decision.reason
```

简单记：

```text
self = 当前这个对象本身
```

---

## 14. `def ttft(self) -> float | None:` 的含义

```python
def ttft(self) -> float | None:
```

这行代码表示定义一个方法，方法名叫 `ttft`。

其中：

```python
self
```

表示当前对象自己。

```python
-> float | None
```

表示这个方法的返回值要么是 `float`，要么是 `None`。

例如：

```python
@property
def ttft(self) -> float | None:
    if self.first_token_time is None:
        return None
    return max(0.0, self.first_token_time - self.start_time)
```

如果 `first_token_time` 是 `None`，说明没有首 token 时间，返回 `None`。

否则返回：

```python
first_token_time - start_time
```

这个结果是浮点数。

所以返回类型是：

```python
float | None
```

---

## 15. 什么是属性方法 `@property`

`@property` 可以把一个方法包装成像属性一样访问。

普通方法调用方式是：

```python
m.ttft()
```

加了 `@property` 后，调用方式变成：

```python
m.ttft
```

看起来就像普通字段。

例如：

```python
@property
def latency(self) -> float:
    return max(0.0, self.end_time - self.start_time)
```

访问时：

```python
m.latency
```

而不是：

```python
m.latency()
```

---

## 16. 为什么 `ttft`、`latency`、`tpot` 适合写成属性方法

因为它们不是原始数据，而是根据原始数据计算出来的派生指标。

原始数据是：

```python
start_time
first_token_time
end_time
output_tokens
```

派生指标是：

```python
ttft
latency
tpot
```

公式是：

```text
ttft = first_token_time - start_time
latency = end_time - start_time
tpot = (end_time - first_token_time) / (output_tokens - 1)
```

如果把 `ttft`、`latency`、`tpot` 也作为字段单独存，可能出现数据不一致。

例如：

```python
start_time = 10.0
end_time = 12.0
latency = 999.0
```

这明显矛盾。

所以更好的方式是只保存原始数据，然后用 `@property` 实时计算派生指标。

这样可以保证：

```text
派生指标永远和原始数据一致
```

---

## 17. 为什么要写 `as_dict`

`as_dict` 的作用是把对象转换成字典。

对象形式：

```python
decision.action
decision.reason
decision.severity
```

字典形式：

```python
{
    "action": "SCALE_OUT",
    "reason": "ttft_p99 too high",
    "severity": "warning"
}
```

很多场景需要字典，而不是对象。

例如：

1. 写日志；
2. 转 JSON；
3. 返回给 API；
4. 传给前端；
5. 传给监控系统；
6. 保存成结构化数据。

例如：

```python
decision.as_dict()
```

可以得到：

```python
{
    "action": "SCALE_OUT",
    "reason": "ttft_p99 too high",
    "desired_replicas": 4,
    "severity": "warning",
    "signals": {
        "ttft_p99": 4.2,
        "gpu_memory_ratio": 0.92,
    },
}
```

如果要转成 JSON，可以继续写：

```python
import json

json.dumps(decision.as_dict())
```

---

## 18. 为什么 `as_dict` 里要写 `self.action.value`

因为：

```python
self.action
```

是枚举对象，例如：

```python
ActionName.SCALE_OUT
```

但日志、JSON、接口里通常需要普通字符串：

```python
"SCALE_OUT"
```

所以要写：

```python
self.action.value
```

把枚举对象转换成字符串值。

---

## 19. 三个类的作用总结

### `RequestMetrics`

表示单个请求的指标。

包括：

```text
请求 ID
租户 ID
工作负载类型
输入 token 数
输出 token 数
开始时间
首 token 时间
结束时间
状态码
错误原因
重试次数
是否流式输出
```

它还提供派生指标：

```text
ttft：首 token 延迟
latency：端到端总延迟
tpot：每个输出 token 的平均耗时
```

---

### `ControllerMetrics`

表示控制器看到的整体系统指标。

包括：

```text
排队时间 p95 / p99
TTFT p95 / p99
TPOT p95 / p99
端到端延迟 p99
等待请求数
运行请求数
GPU 显存占用率
GPU 利用率
输入 token 吞吐
输出 token 吞吐
错误率
超时率
当前副本数
长上下文请求比例
租户过载比例
缺失指标列表
```

---

### `Decision`

表示控制器做出的决策。

包括：

```text
action：动作
reason：原因
desired_replicas：期望副本数
severity：严重程度
signals：触发该决策的关键信号
```

例如：

```python
decision = Decision(
    action=ActionName.SCALE_OUT,
    reason="ttft_p99 exceeds target",
    desired_replicas=4,
    severity="warning",
    signals={
        "ttft_p99": 4.2,
        "gpu_memory_ratio": 0.92,
        "current_replicas": 2,
    },
)
```

---

## 20. 最核心规则总结

```text
类 class：模板
对象 object：根据模板创建出来的具体东西
实例 instance：对象的另一种说法
实例化：用类创建对象的过程
属性：对象里存的数据
方法：对象能调用的函数
self：当前对象自己
```

```text
字段后面没有默认值：创建对象时必须传
字段后面有默认值：可以不传，传了就覆盖默认值
```

```text
int / float / str / bool / None 是不可变对象，可以直接作为默认值
list / dict / set 是可变对象，默认值要用 field(default_factory=...)
```

```text
Enum 是固定选项集合，用来防止字符串乱写
str, Enum 表示这个枚举既是枚举，又以字符串作为底层值
```

```text
@property 用来把计算方法包装成属性
ttft、latency、tpot 这类派生指标适合写成属性方法
```

```text
as_dict 用来把对象转换成字典，方便写日志、转 JSON、返回 API、传给前端或监控系统
```

这段代码整体是在做大模型推理服务控制器的数据建模：

```text
RequestMetrics：单个请求的原始指标和派生指标
ControllerMetrics：系统整体监控指标
ActionName：控制器允许输出的动作集合
Decision：控制器最终做出的决策
```
"""

