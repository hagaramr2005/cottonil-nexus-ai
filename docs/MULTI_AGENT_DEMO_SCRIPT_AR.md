# سيناريو تصوير فيديو الـ Multi-Agent AI — LinkedIn

**الفكرة:** دقيقة إلى دقيقتين، ونتكلم عن تنفيذ شغال فعلًا مش مجرد رسم للـ Architecture.

1. **0–15 ثانية:** افتحي Dashboard وأوضحي على الشاشة عبارة **SYNTHETIC DEMO DATA — NOT REAL COTTONIL METRICS** لو مستخدمة داتا التجربة. قولي إن ده Training Project بيوضح Decision Intelligence.
2. **15–35 ثانية:** انتقلي للـ AI Copilot واسألي بالإنجليزي `What is the net sales in the synthetic demo?`. افتحي `View AI Agent Workflow` واشرحي انتقال السؤال من Supervisor إلى Sales Analyst ثم Grounding Reviewer ثم Narrative Agent.
3. **35–60 ثانية:** اسألي `ما أهم التحقيقات المسجلة في البيانات التجريبية؟` وافتحي تفاصيل الـ Agent Trace. وضحي إن Risk Investigator بيسترجع فقط الحالات الموجودة بالفعل، ومش بيعتبر الفرضيات خسائر مؤكدة.
4. **60–80 ثانية:** اسألي `What is the exact confirmed financial loss?`، ووضحي إن النظام بيرفض اختراع مبلغ لو مصدر البيانات ما يثبتوش. دي أهم نقطة لـ Trustworthy AI.
5. **80–100 ثانية:** لو Ollama اشتغل فعليًا، ورّي رد فيه `grounded-llm` و`llm_used=true` بعد اختبار السؤال المدعوم. لو ما اشتغلش، وضحي إن ده Safe Fallback بدل ما تدّعي إن الموديل اشتغل.
6. **النهاية:** اذكري باختصار React + FastAPI + SQLite + Ollama + RBAC + Evidence Grounding، وإن الـ Multi-Agent مبني كـ Bounded Role-Based Orchestration عشان يبقى قابل للاختبار على جهاز محلي.

## وصف مناسب للمشروع بالإنجليزي

**COTTONIL NEXUS AI — Multi-Agent Retail Intelligence Prototype**

Built a bilingual, evidence-first AI Copilot with a lightweight multi-agent orchestration layer. A Supervisor routes requests, specialist agents validate sales metrics and investigation evidence, a Grounding Reviewer enforces safety and data sufficiency, and an optional local Ollama model generates the final narrative. Every response exposes an execution trace, sources, and a transparent fallback mode. Demonstrated with clearly labeled synthetic data as part of a training portfolio project — not a production client deployment.

**لا تنشري أي داتا شركة أو Credentials في الفيديو**، وتأكدي من تجربة السؤال قبل التصوير.
