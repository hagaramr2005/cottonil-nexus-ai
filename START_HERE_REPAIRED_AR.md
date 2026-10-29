# COTTONIL NEXUS AI — النسخة الكاملة مع إصلاحات الـ Copilot

## اقرأ قبل التسليم

هذه **نسخة مشروع كاملة** مبنية على أرشيف `COTTONIL_NEXUS_AI_V13_SECURITY_HARDENED_NOT_YET_PRODUCTION.zip` الذي كان متاحًا في المحادثة، مع دمج إصلاحات `COTTONIL_COPILOT_V13_REPAIR_PACKAGE.zip`. تحتوي على Backend وFrontend وقاعدة SQLite وبيانات المصدر المضغوطة والاختبارات والوثائق.

**ليست** نسخة من ملفات جهازك بعد تعديلات OpenCode الأحدث، لأن هذه الملفات لم تُرفع في المحادثة. لا تستبدل بها مجلد OpenCode الحالي مباشرة. استخدم مجلدًا منفصلًا وقارن التعديلات قبل الدمج. **لا يصح وصف هذه النسخة بأنها Production Ready أو جاهزة للتسليم دون التشغيل على جهازك.**

## اختبارات تم تشغيلها على هذه النسخة

- `PYTHONPATH=backend pytest -q backend/tests --disable-warnings` — **69 passed** في بيئة Linux المعزولة، بعد تعديل فحص PDF للتأكد من تضمين خط TrueType حقيقي مع السماح بخط محلي بديل.
- `python -m compileall -q backend/app` — ناجح.
- فحص `normalizeApiPath` باستخدام Node.js — ناجح في حالات `/api` المتكرر.
- **لم يتم التحقق:** إنتاج Frontend عبر `npm run build` أو اختبارات Vitest/Playwright أو المتصفح على Windows أو اتصال فعلي بموديل Qwen عبر Ollama في هذه البيئة. تعذّر إكمال `npm ci` هنا.

## ملاحظات ملفات الخطوط

ملفات الخطوط الثنائية `.ttf` لم تُرفق بهذه النسخة. تصدير PDF أصبح يحاول استخدام خطوط عربية متوافقة متاحة على Windows أو Linux، ويستخدم ملفات المشروع الأصلية إن كانت موجودة محليًا. قد تختلف هوية الخط في PDF عن النسخة الأصلية؛ وللحفاظ على تنسيق IBM Plex Sans Arabic نفسه يمكن الإبقاء على الخطوط المثبتة محليًا في مجلد المشروع الأصلي على جهازك. الحزمة تحتوي على بقية الأصول ولا تحتوي على `.venv` أو `node_modules`؛ يتم تثبيتهما محليًا.

## تشغيل Windows PowerShell

افتح مجلد `cottonil-nexus-ai-v10` المستخرج. استخدم Python 3.12 على Windows، ثم:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

تأكدي إن Ollama شغال والموديل متحمّل:

```powershell
ollama list
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

Terminal أولى (Backend):

```powershell
.\.venv\Scripts\Activate.ps1
$env:NEXUS_LLM_URL='http://127.0.0.1:11434/v1/chat/completions'
$env:NEXUS_LLM_MODEL='qwen2.5:3b'
python -m uvicorn app.main:app --app-dir backend --port 8001
```

Terminal ثانية (Frontend) في مجلد المشروع المستخرج:

```powershell
cd frontend
npm ci
$env:NEXUS_API='http://127.0.0.1:8001'
npm run dev
```

افتح رابط `Local` الذي يظهر (قد يكون 5173 أو 5174 أو 5175).

## فحوص التشغيل المحلي المطلوبة قبل التسليم

```powershell
$env:PYTHONPATH='backend'
python -m pytest -q backend\tests
```

من `frontend`:

```powershell
npm run test
npm run build
```

من جذر المشروع مع تشغيل Frontend/Backend:

```powershell
.\scripts\verify_copilot_v14.ps1 -ApiBase 'http://127.0.0.1:8001' -FrontendBase 'http://localhost:5174'
```

بدّلي 5174 بالمنفذ الفعلي. يتطلب وضع المصادقة تهيئة توكن مصرح له للاختبار؛ راجعي `docs/COPILOT_FIX_V13_SNAPSHOT_REPORT.md`.

## ما الذي لم يكتمل؟

- حفظ المحادثات في قاعدة بيانات لعدة مستخدمين والأجهزة المختلفة غير مطبق. يوجد سياق مؤقت ضمن المحادثة الحالية.
- تمرير فلاتر التاريخ والفرع والمنتج التفصيلية للـ Copilot لم يكتمل.
- لم يتم التحقق من تشغيل Frontend بالمستعرض أو من اتصال Ollama الحقيقي في بيئة الدمج.
- الإصلاحات ليست ضمانًا ضد الهلوسة أو تنفيذًا لنظام إنتاجي كامل.

**التسليم للعميل يحتاج مراجعة أحدث نسخة OpenCode التي في جهازك، وتشغيل Browser QA وبناء Frontend محليًا.**
