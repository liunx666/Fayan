from langchain_core.runnables import RunnableGenerator
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from starlette.responses import StreamingResponse

# ========== 【使用官方流式透传工具】 ==========
async def stream_translator(input_iter):
    async for msg in input_iter:
        yield msg.content

# 流式透传Runnable，替代自定义Parser，无签名bug
stream_parser = RunnableGenerator(stream_translator)

model = ChatOpenAI(
    model="deepseek-v4-flash",
    base_url="https://api.deepseek.com/v1",
    api_key="你的apikey",
    temperature=0.0,
    streaming=True,
    stream_usage=False,
    # 独有扩展参数放 extra_body
    extra_body={
        "thinking": {"type": "disabled"}
    },
    model_kwargs={
        "stream_options": {"include_usage": False}
    }
)

# 合同审查提示词
review_prompt = """
你是一位资深商业律师，负责审查合同文本。你的任务是从用户提供的合同内容中，找出所有对甲方（用户方）有潜在风险的条款，并严格按以下格式返回结果。

【强制优先级规则，必须第一时间遵守】
优先级1：原文一字不改，禁止增删、改写、润色任何文字；
优先级2：区分句子类型，同一单句只能使用一种标签，不可同时加<mark>和<safe>；
优先级3：逐句流式生成输出，禁止缓存整段统一输出；
优先级4：禁止任何多余文字，仅输出打标后的合同正文。

【审查执行细则，严禁违反】
1. 句子存在甲方风险：仅对风险原文使用 <mark>风险原文</mark> 包裹，紧跟 <risk>风险说明</risk>，标签必须成对完整闭合，格式不能错乱；
2. 句子无任何风险、权责对等、表述清晰：整句完整包裹 <safe>句子全文</safe>，标签成对闭合；
3. 无风险内容必须原封不动原样输出，禁止增删、修改、润色、删减任何原文文字；
4. 禁止输出任何前置话术、结尾总结、分析报告、多余解释，只输出处理后的合同正文；
5. 全程逐句生成、逐段流式输出，禁止模型缓存整段内容后一次性输出；
6. 风险说明简洁客观，只说明风险点，不扩写、不废话。

【举例识别以下6类甲方风险，如有其他风险请继续标注】
- 不合理的违约金比例
- 单方面解约权
- 模糊的付款或交付时间
- 无限责任条款
- 过高或异常的押金、保证金
- 自动续约条款

【输出格式标准示例，严格复刻】
示例1（风险句子）
原句：如果乙方逾期，每天罚5%。
输出：如果乙方逾期，<mark>每天罚5%</mark><risk>违约金比例过高，建议谈判降低</risk>。

示例2（安全句子）
原句：甲方应于收到货物后7个工作日内完成验收。
输出：<safe>甲方应于收到货物后7个工作日内完成验收。</safe>

示例3（同一段落混合安全+风险，逐句分开打标）
原文：甲方收货7日内验收。若甲方逾期付款每日收取8%违约金。
标准输出：
<safe>甲方收货7日内验收。</safe>
若甲方逾期付款<mark>每日收取8%违约金</mark><risk>违约金比例过高，加重甲方负担</risk>。

严格按照上述全部规则处理合同，不自由发挥、不额外添字、不缓存内容，逐段实时流式输出。
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", review_prompt),
    ("user", "{contract_text}"),
])

# 构建流式链路
review_chain = (
    RunnablePassthrough()
    | prompt
    | model
    | stream_parser
)

# 纯异步流式接口
async def stream_review_contract(contract_text: str) -> StreamingResponse:
    async def real_stream_generator():
        async for chunk in review_chain.astream({"contract_text": contract_text}):
            if chunk and chunk.strip():
                yield chunk

    return StreamingResponse(
        content=real_stream_generator(),
        media_type="text/plain; charset=utf-8",
        headers={
            "Transfer-Encoding": "chunked",
            "X-Transfer-Encoding": "chunked",
            "Cache-Control": "no-cache, no-store, must-revalidate, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )
