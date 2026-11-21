# Partner03 流式输出知识注解

本文对应 `Partner03.py` 中的三个知识点：

1. `with` 的作用。
2. `getattr()` 的作用。
3. `st.empty()` 返回的空容器，以及为什么可以调用 `.markdown()`。

## 1. with 的作用

### 代码

```python
with st.chat_message("assistant"):
    reasoning_placeholder = st.empty()
    content_placeholder = st.empty()
```

### 普通理解

`with` 可以理解成“创建一个容器，并把缩进区域内的内容放进容器里”。

这里的容器是一个助手消息气泡。只要代码保持缩进，下面创建的
`st.empty()` 和后面输出的文字，都会属于这个助手消息。

```python
with st.chat_message("assistant"):
    st.write("第一行")
    st.write("第二行")
```

页面效果可以理解为：

```text
助手头像
    第一行
    第二行
```

### 不用 with 的写法

如果不使用 `with`，可以手动创建一个助手气泡对象，再往里面添加内容：

```python
assistant = st.chat_message("assistant")

reasoning_placeholder = assistant.empty()
content_placeholder = assistant.empty()
```

这段代码和使用 `with` 的效果基本一样。使用 `with` 的好处是缩进关系更清楚，
看到缩进就能知道哪些内容属于当前助手气泡。

### 为什么离开 with 后还要写 session_state

`with` 只管 Streamlit 页面上的显示区域。

```python
with st.chat_message("assistant"):
    content_placeholder.markdown(answer_content)
```

这段代码只负责把答案显示到页面上。它不会自动保存对话历史。

所以离开 `with` 后，还需要把答案加入 `session_state`：

```python
st.session_state.messages.append({
    "role": "assistant",
    "content": answer_content
})
```

前者负责“显示”，后者负责“记忆”。

## 2. getattr 的作用

### 代码

```python
reasoning_piece = getattr(delta, "reasoning_content", None)
answer_piece = getattr(delta, "content", None)
```

### 平时读取属性的方式

平时使用点号读取对象属性：

```python
delta.content
delta.reasoning_content
```

如果属性存在，点号可以正常读取：

```python
value = delta.content
```

如果属性不存在，点号会直接抛出 `AttributeError`：

```python
value = delta.reasoning_content
# AttributeError
```

### getattr 的三个参数

`getattr()` 的格式是：

```python
getattr(对象, "属性名", 默认值)
```

它的规则是：

1. 属性存在，返回属性值。
2. 属性不存在，返回默认值。

所以：

```python
getattr(delta, "reasoning_content", None)
```

可以理解为：

```python
try:
    reasoning_piece = delta.reasoning_content
except AttributeError:
    reasoning_piece = None
```

### 为什么流式返回需要 getattr

流式响应中的 chunk 结构不完全一样。

推理阶段的 chunk 可能长这样：

```python
{
    "content": None,
    "reasoning_content": "正在分析问题"
}
```

回答阶段的 chunk 可能长这样：

```python
{
    "content": "你好",
    "reasoning_content": None
}
```

有些 chunk 甚至可能没有其中某个字段。使用 `getattr()` 后，无论字段是否存在，
代码都能安全地拿到 `None` 或真实内容，不容易因为属性缺失而报错。

## 3. st.empty 和 markdown 的作用

### 代码

```python
reasoning_placeholder = st.empty()
content_placeholder = st.empty()
```

### st.empty 返回的不是 None

`st.empty()` 会在 Streamlit 页面中预留一个位置，并返回一个容器对象。

可以把它想成一块预留的白板：

```text
页面：
[预留位置]
```

这个容器对象可以调用多种 Streamlit 方法：

```python
placeholder.markdown("内容")
placeholder.write("内容")
placeholder.text("内容")
placeholder.code("代码")
```

### 为什么能调用 markdown

因为 `placeholder` 是一个 Streamlit 容器对象，`.markdown()` 是这个对象提供的
方法。调用它的意思是：

```text
把预留位置中的内容替换成 Markdown 文本
```

示例：

```python
placeholder = st.empty()

placeholder.markdown("你")
placeholder.markdown("你好")
placeholder.markdown("你好，世界")
```

页面最终只显示：

```text
你好，世界
```

前面的内容不是消失了，而是被同一个预留位置的新内容覆盖了。

### 和直接使用 st.markdown 的区别

直接调用 `st.markdown()` 会不断创建新元素：

```python
st.markdown("你")
st.markdown("你好")
st.markdown("你好，世界")
```

页面会显示三行：

```text
你
你好
你好，世界
```

使用空容器更新时，只会保留最后一次：

```python
placeholder = st.empty()

placeholder.markdown("你")
placeholder.markdown("你好")
placeholder.markdown("你好，世界")
```

页面只显示：

```text
你好，世界
```

### 为什么流式输出需要这样做

流式响应每轮只返回一小段内容：

```text
你
好
，
世
界
```

代码先把片段累加成完整内容：

```python
answer_content += answer_piece
```

再使用同一个空容器覆盖显示：

```python
content_placeholder.markdown(answer_content + "▌")
```

页面变化过程可以理解为：

```text
你▌
你好▌
你好，▌
你好，世▌
你好，世界▌
```

最后去掉光标：

```python
content_placeholder.markdown(answer_content)
```

最终显示：

```text
你好，世界
```

## 完整流程

```python
with st.chat_message("assistant"):
    reasoning_placeholder = st.empty()
    content_placeholder = st.empty()

    reasoning_content = ""
    answer_content = ""

    for chunk in response:
        delta = chunk.choices[0].delta

        reasoning_piece = getattr(delta, "reasoning_content", None)
        answer_piece = getattr(delta, "content", None)

        if reasoning_piece:
            reasoning_content += reasoning_piece
            reasoning_placeholder.markdown(reasoning_content)

        if answer_piece:
            answer_content += answer_piece
            content_placeholder.markdown(answer_content + "▌")

    content_placeholder.markdown(answer_content)
```

流程总结：

1. `with` 创建一个助手消息气泡。
2. `st.empty()` 在气泡内预留显示位置。
3. `getattr()` 安全读取每个流式 chunk 中的内容字段。
4. 每收到一小段，就把它加到完整字符串中。
5. 使用同一个占位容器覆盖旧内容，形成流式输出效果。
