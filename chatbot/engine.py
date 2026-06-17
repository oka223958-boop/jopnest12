"""
    "javascript", "typescript", "java", "kotlin", "swift",
    "machine learning", "deep learning", "tensorflow", "pytorch",
    "cybersecurity", "security", "linux", "docker", "kubernetes",
    "aws", "azure", "google cloud", "cloud", "devops", "firebase", "mongodb",
    "postgresql", "redis", "git", "php", "laravel", "vue", "angular",
    "nextjs", "next.js", "figma", "photoshop", "illustrator", "canva",
    "data science", "artificial intelligence", "nlp",
    "frontend", "backend", "fullstack", "mobile", "android", "ios",
    "beginner", "intermediate", "advanced", "course", "courses",
    "roadmap", "track", "certificate",
]


def correct_typos(message: str):
    from difflib import get_close_matches
    corrected = message.lower()
    corrections = []

    # Step 1: hardcoded dict (word-boundary match to avoid "javascrip" inside "javascript")
    for wrong, right in COMMON_TYPOS.items():
        if re.search(r'\b' + re.escape(wrong) + r'\b', corrected):
            corrections.append((wrong, right))
            corrected = re.sub(r'\b' + re.escape(wrong) + r'\b', right, corrected)

    # Step 2: fuzzy matching word by word
    words = corrected.split()
    fuzzy_corrected = []
    for word in words:
        clean = re.sub(r"[^\w]", "", word)
        if len(clean) < 4 or clean in KNOWN_TECH_WORDS or clean in PROTECTED_WORDS:
            fuzzy_corrected.append(word)
            continue
        match = get_close_matches(clean, KNOWN_TECH_WORDS, n=1, cutoff=0.75)
        if match and match[0] != clean:
            corrections.append((clean, match[0]))
            fuzzy_corrected.append(match[0])
        else:
            fuzzy_corrected.append(word)

    corrected = " ".join(fuzzy_corrected)
    return corrected, corrections


# ─────────────────────────────────────────────────────────────
#  KEYWORD LISTS
# ─────────────────────────────────────────────────────────────

JOB_KEYWORDS = [
    "find job", "find jobs", "show me jobs", "job opportunities", "job openings",
    "jobs for", "jobs in", "hiring", "vacancy", "career opportunities",
    "وظيفة", "وظايف", "شغل", "فرصة عمل", "فرص عمل", "عايز اشتغل", "دور على شغل",
    "job", "jobs", "work", "career", "position", "vacancy",
]

COURSE_KEYWORDS = [
    "recommend courses", "suggest courses", "best courses", "courses for",
    "courses to learn", "where to learn", "learning resources",
    "كورس", "كورسات", "تعلم", "دورة", "دورات", "اتعلم", "مسار", "تراك",
    "course", "courses", "learn", "tutorial", "training", "certificate",
    "track", "path", "roadmap",
]

SKILLS_KEYWORDS = [
    "what skills", "skills needed", "skills required", "what do i need to learn",
    "skills for", "what to learn for", "skills to become",
    "ايه السكيلز", "مهارات", "سكيلز", "ايه اللي محتاج",
]

GENERAL_KEYWORDS = [
    "what is", "what are", "explain", "difference between", "vs",
    "how does", "tell me about", "define",
    "ما هو", "ما هي", "اشرح", "الفرق بين", "ايه هو",
]

CV_KEYWORDS = [
    "cv", "سيرة ذاتية", "ريزومي", "resume",
    "cv tips", "improve cv", "write cv", "review cv",
]

GREETING_KEYWORDS = [
    "هاي", "هلو", "مرحبا", "السلام عليكم", "اهلا", "أهلا",
    "صباح الخير", "مساء الخير", "ازيك",
    "hi", "hello", "hey", "good morning", "how are you", "greetings",
]

COMPANY_KEYWORDS = [
    "موظف", "توظيف", "عايز اوظف", "ابحث عن موظف",
    "hire", "recruit", "find candidate", "find developer", "looking for employee",
]

LOCATION_KEYWORDS = [
    "cairo", "القاهرة", "alexandria", "الاسكندرية",
    "giza", "الجيزة",
    "mansoura", "المنصورة",
]

# Arabic → English location aliases (the dataset stores English city names)
LOCATION_ALIASES = {
    "القاهرة"   : "cairo",
    "الاسكندرية": "alexandria",
    "الجيزة"    : "giza",
    "المنصورة"  : "mansoura",
}

JOBTYPE_KEYWORDS = {
    "remote"    : ["remote", "ريموت", "من البيت", "online", "work from home"],
    "full time" : ["full time", "fulltime", "دوام كامل", "full-time"],
    "part time" : ["part time", "parttime", "دوام جزئي", "part-time"],
    "internship": ["internship", "intern", "تدريب", "junior", "entry level", "entry-level"],
    "hybrid"    : ["hybrid", "هايبرد"],
    "freelance" : ["freelance", "فريلانس", "مستقل"],
}

LEVEL_KEYWORDS = {
    "Beginner"    : ["beginner", "مبتدئ", "from scratch", "من الصفر", "zero", "start", "new to", "just started"],
    "Intermediate": ["intermediate", "متوسط", "some experience"],
    "Advanced"    : ["advanced", "متقدم", "expert", "senior", "professional"],
}

ARABIC_KW = ["عربي", "بالعربي", "arabic"]
FREE_KW    = ["مجاني", "مجانا", "free", "بالمجان", "no cost", "مفيش فلوس"]

SKILLS_POOL = [
    "python", "flutter", "dart", "react", "node", "django", "fastapi",
    "javascript", "typescript", "java", "kotlin", "swift",
    "sql", "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
    "cyber", "security", "kali", "figma", "photoshop", "illustrator",
    "docker", "kubernetes", "aws", "azure", "cloud", "devops",
    "firebase", "mongodb", "postgresql", "redis", "git", "linux",
    "php", "laravel", "vue", "angular", "nextjs", "next.js",
]

MISSING_INFO_FOLLOWUP = {
    "job_search"   : "في مدينة معينة أو نوع شغل تفضله؟ (Remote / Cairo / Hybrid)",
    "course_search": "عايز Beginner ولا Advanced؟ وبالعربي ولا إنجليزي؟",
}


# ─────────────────────────────────────────────────────────────
#  INTENT DETECTION
# ─────────────────────────────────────────────────────────────

def detect_specialty(msg: str):
    for specialty, data in SPECIALTY_TRACKS.items():
        if any(kw in msg for kw in data["keywords"]):
            return specialty
    return None


def detect_goal_track(msg: str):
    for goal, data in GOAL_TRACKS.items():
        if any(kw in msg for kw in data["keywords"]):
            return goal
    return None


def detect_general(msg: str):
    for key, data in GENERAL_KNOWLEDGE.items():
        if any(kw in msg for kw in data["keywords"]):
            return key
    return None


def detect_career_advice(msg: str):
    for key, data in CAREER_ADVICE.items():
        if any(kw in msg for kw in data["keywords"]):
            return key
    return None


def detect_social(msg: str):
    for key, data in SOCIAL_RESPONSES.items():
        if any(kw in msg for kw in data["keywords"]):
            return key
    return None


def detect_skills_question(msg: str):
    return any(kw in msg for kw in SKILLS_KEYWORDS)


def detect_intent(message: str) -> dict:
    msg = message.lower().strip()
    corrected_msg, corrections = correct_typos(msg)
    if corrections:
        msg = corrected_msg

    # fast-path detections
    specialty    = detect_specialty(msg)
    goal_track   = detect_goal_track(msg)
    general_key  = detect_general(msg)
    career_key   = detect_career_advice(msg)
    social_key   = detect_social(msg)
    skills_q     = detect_skills_question(msg)

    scores = {
        "track_specialty" : 3 if specialty  else 0,
        "track_goal"      : 3 if goal_track else 0,
        "general_knowledge": 4 if general_key else 0,
        "career_advice"   : 3 if career_key  else 0,
        "social"          : 2 if social_key  else 0,
        "skills_question" : 2 if skills_q    else 0,
        "job_search"      : 0,
        "course_search"   : 0,
        "cv_help"         : 0,
        "company_search"  : 0,
        "greeting"        : 0,
    }

    for kw in JOB_KEYWORDS:
        if kw in msg: scores["job_search"] += 2
    for kw in COURSE_KEYWORDS:
        if kw in msg: scores["course_search"] += 2
    for kw in CV_KEYWORDS:
        if kw in msg: scores["cv_help"] += 2
    for kw in GREETING_KEYWORDS:
        if kw in msg: scores["greeting"] += 2
    for kw in COMPANY_KEYWORDS:
        if kw in msg: scores["company_search"] += 2
    for kw in GENERAL_KEYWORDS:
        if kw in msg: scores["general_knowledge"] += 1

    # specialty + course keyword together = track
    if specialty and scores["course_search"] > 0:
        scores["track_specialty"] += 2

    # explicit job-search wins over specialty-track: if the user said
    # "I want a job in flutter" they want jobs, not a learning roadmap.
    if scores["job_search"] >= 2 and scores["track_specialty"] > 0:
        scores["job_search"]    += 3
        scores["track_specialty"] = max(0, scores["track_specialty"] - 2)

    skills   = [sk for sk in SKILLS_POOL if re.search(r'\b' + re.escape(sk) + r'\b', msg)]
    location = next((loc for loc in LOCATION_KEYWORDS if loc in msg), None)
    job_type = next((jt for jt, kws in JOBTYPE_KEYWORDS.items()
                     if any(k in msg for k in kws)), None)
    level    = next((lvl for lvl, kws in LEVEL_KEYWORDS.items()
                     if any(k in msg for k in kws)), None)
    language = "Arabic" if any(k in msg for k in ARABIC_KW) else None
    free     = any(k in msg for k in FREE_KW)

    if skills and all(scores[k] == 0 for k in
                      ["job_search","course_search","track_specialty","general_knowledge"]):
        scores["job_search"]    += 1
        scores["course_search"] += 1

    intent = max(scores, key=scores.get)
    if scores[intent] == 0:
        intent = "unknown"

    confidence = min(1.0, round(scores.get(intent, 0) / 6.0, 2))

    return {
        "intent"     : intent,
        "specialty"  : specialty,
        "goal_track" : goal_track,
        "general_key": general_key,
        "career_key" : career_key,
        "social_key" : social_key,
        "skills_q"   : skills_q,
        "skills"     : skills,
        "location"   : location,
        "job_type"   : job_type,
        "level"      : level,
        "language"   : language,
        "free"       : free,
        "corrections": corrections,
        "confidence" : confidence,
        "raw"        : message,
    }


# ─────────────────────────────────────────────────────────────
#  CHATBOT ENGINE
# ─────────────────────────────────────────────────────────────

class ChatbotEngine:

    def __init__(self, jobs, users, courses, engine):
        from utils.data_loader import _fix_experience
        if jobs is not None and "experience_required" in jobs.columns:
            jobs = jobs.copy()
            jobs["experience_required"] = jobs["experience_required"].apply(_fix_experience)
        self.jobs    = jobs
        self.users   = users
        self.courses = courses
        self.engine  = engine
        log.info("ChatbotEngine v3.0 initialized")

    def chat(self, message: str, user_id: int = None,
             top_n: int = 5, context: list = None) -> dict:

        parsed  = detect_intent(message)
        intent  = parsed["intent"]
        context = context or []

        # personalization
        user_name = None
        if user_id:
            u = self.users[self.users["user_id"] == user_id]
            if not u.empty:
                user_name = str(u.iloc[0]["user_name"]).split()[0]

        # typo note
        correction_note = ""
        if parsed["corrections"]:
            fixes = ", ".join([f"{o} -> {n}" for o, n in parsed["corrections"]])
            correction_note = f"(تصحيح: {fixes}) "

        # dispatch
        dispatch = {
            "greeting"         : lambda: self._reply_greeting(user_name),
            "social"           : lambda: self._reply_social(parsed),
            "general_knowledge": lambda: self._reply_general(parsed, user_name),
            "career_advice"    : lambda: self._reply_career_advice(parsed, top_n, user_name),
            "skills_question"  : lambda: self._reply_skills(parsed, user_name),
            "track_specialty"  : lambda: self._handle_specialty_track(parsed, top_n, user_name),
            "track_goal"       : lambda: self._handle_goal_track(parsed, top_n, user_name),
            "job_search"       : lambda: self._handle_job_search(parsed, user_id, top_n, user_name),
            "course_search"    : lambda: self._handle_course_search(parsed, top_n, user_name, context),
            "cv_help"          : lambda: self._reply_cv_help(user_name),
            "company_search"   : lambda: self._handle_company_search(parsed, top_n),
        }

        result = dispatch.get(intent, lambda: self._reply_unknown())()

        if correction_note:
            result["reply"] = correction_note + result["reply"]

        conf = parsed["confidence"]
        result["confidence"]       = conf
        result["confidence_label"] = ("مناسبة جداً ليك ✨" if conf >= 0.8
                                       else "مناسبة ليك 👍" if conf >= 0.5
                                       else "قد تكون مناسبة ليك")
        return result

    # ── Social ────────────────────────────────────────────────
    def _reply_social(self, parsed):
        key  = parsed["social_key"]
        data = SOCIAL_RESPONSES.get(key, {})
        reply = data.get("reply") or None
        if not reply:
            return self._reply_unknown()
        return {"intent": "social", "reply": reply,
                "type": "text", "count": 0, "results": [], "follow_up": None}

    # ── General Knowledge ─────────────────────────────────────
    def _reply_general(self, parsed, user_name):
        key    = parsed["general_key"]
        data   = GENERAL_KNOWLEDGE.get(key, {})
        answer = data.get("answer", "مش عندي معلومات كافية عن ده دلوقتي.")
        greeting = f"{user_name}، " if user_name else ""
        return {
            "intent"    : "general_knowledge",
            "reply"     : greeting + answer,
            "type"      : "text",
            "count"     : 0,
            "results"   : [],
            "follow_up" : "عايز تعرف أكتر أو تشوف كورسات في الموضوع ده؟",
        }

    # ── Career Advice ─────────────────────────────────────────
    def _reply_career_advice(self, parsed, top_n, user_name):
        key      = parsed["career_key"]
        data     = CAREER_ADVICE.get(key, {})
        advice   = data.get("advice", "قولي أكتر عن خبرتك وهساعدك!")
        greeting = f"{user_name}، " if user_name else ""
        specialty = data.get("specialty") or parsed["specialty"]

        # اقترح كورسات لو في تخصص محدد
        results   = []
        follow_up = None
        if specialty:
            filtered  = self.courses[self.courses["specialty"].str.lower() == specialty.lower()]
            results   = filtered.sort_values("rating", ascending=False).head(top_n).to_dict(orient="records")
            follow_up = f"عايز تشوف وظايف في {specialty}؟"

        return {
            "intent"    : "career_advice",
            "reply"     : greeting + advice,
            "type"      : "courses" if results else "text",
            "count"     : len(results),
            "results"   : _fmt_courses(results),
            "follow_up" : follow_up,
        }

    # ── Skills Question ───────────────────────────────────────
    def _reply_skills(self, parsed, user_name):
        specialty = parsed["specialty"]
        greeting  = f"{user_name}، " if user_name else ""

        if specialty:
            data   = SPECIALTY_TRACKS[specialty]
            skills = data["skills_required"]
            roles  = data["career_roles"]
            reply  = (f"{greeting}المهارات المطلوبة لـ {data['description']}:\n\n"
                      f"Skills: {' | '.join(skills)}\n\n"
                      f"Career Roles: {', '.join(roles)}")
        else:
            reply = (f"{greeting}ذكرلي التخصص اللي مهتم بيه وهقولك المهارات المطلوبة!\n"
                     "مثال: 'What skills do I need for AI?' أو 'ايه السكيلز للفلاتر؟'")

        return {
            "intent"    : "skills_question",
            "reply"     : reply,
            "type"      : "text",
            "count"     : 0,
            "results"   : [],
            "follow_up" : f"عايز تشوف كورسات {specialty}؟" if specialty else None,
        }

    # ── Specialty Track ───────────────────────────────────────
    def _handle_specialty_track(self, parsed, top_n, user_name):
        specialty = parsed["specialty"]
        track     = SPECIALTY_TRACKS[specialty]
        greeting  = f"{user_name}، " if user_name else ""
        all_results, stage_info = [], []

        for stage in track["stages"]:
            level, focus = stage["level"], stage["focus"]
            filtered = self.courses[
                (self.courses["specialty"].str.lower() == specialty.lower()) &
                (self.courses["level"].str.lower()     == level.lower())
            ]
            if not filtered.empty:
                mask = filtered["skills"].apply(
                    lambda x: any(f.lower() in str(x).lower() for f in focus))
                if mask.sum() > 0: filtered = filtered[mask]
            if parsed.get("language"):
                lm = filtered["language"] == parsed["language"]
                if lm.sum() > 0: filtered = filtered[lm]

            top = filtered.sort_values("rating", ascending=False).head(2)
            all_results.extend(top.to_dict(orient="records"))
            stage_info.append({"stage": level, "focus": " | ".join(focus), "courses": len(top)})

        count = len(all_results)
        return {
            "intent"      : "track_specialty",
            "reply"       : (f"{greeting}مسار {track['description']} الكامل! 🎯\n"
                             f"فيه {count} كورس موزعين: Beginner → Intermediate → Advanced\n\n"
                             f"نبذة: {track['summary']}"),
            "type"        : "track",
            "specialty"   : specialty,
            "track_stages": stage_info,
            "count"       : count,
            "results"     : _fmt_courses(all_results),
            "follow_up"   : "عايز تفلتر بلغة معينة أو منصة معينة؟",
        }

    # ── Goal Track ────────────────────────────────────────────
    def _handle_goal_track(self, parsed, top_n, user_name):
        goal     = parsed["goal_track"]
        track    = GOAL_TRACKS[goal]
        greeting = f"{user_name}، " if user_name else ""
        filtered = self.courses.copy()

        if parsed["specialty"]:
            mask = filtered["specialty"].str.lower() == parsed["specialty"].lower()
            if mask.sum() > 0: filtered = filtered[mask]

        results = filtered.sort_values("rating", ascending=False).head(top_n)
        steps   = "\n".join([f"  {i+1}. {s}" for i, s in enumerate(track["stages"])])

        return {
            "intent"    : "track_goal",
            "reply"     : (f"{greeting}مسار {track['description']}! 🚀\n"
                           f"الخطوات:\n{steps}\n\nلقيتلك {len(results)} كورس يساعدك تبدأ!"),
            "type"      : "track",
            "goal"      : goal,
            "steps"     : track["stages"],
            "count"     : len(results),
            "results"   : _fmt_courses(results.to_dict(orient="records")),
            "follow_up" : "عايز تحدد تخصص معين في المسار ده؟",
        }

    # ── Job Search ────────────────────────────────────────────
    def _handle_job_search(self, parsed, user_id, top_n, user_name):
        filtered  = self.jobs.copy()
        greeting  = f"{user_name}، " if user_name else ""
        applied   = []  # tracks which filters actually matched data

        # Specialty is a soft hint — narrow if it matches, otherwise ignore
        # (user keywords may not align 1:1 with the `industry` column).
        if parsed["specialty"]:
            mask = filtered["industry"].str.lower() == parsed["specialty"].lower()
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("specialty")

        if parsed["skills"]:
            # Match on skills OR title — dataset sometimes lists "Java Developer"
            # without "Java" in the required_skills column.
            title_hit  = filtered["title"].apply(lambda x: _any_token_match(x, parsed["skills"]))
            skill_hit  = filtered["job_required_skills"].apply(
                lambda x: _any_token_match(x, parsed["skills"]))
            mask = title_hit | skill_hit
            if mask.sum() > 0:
                filtered = filtered[mask].copy()
                # Rank: title matches come first (most relevant to user's query)
                filtered["_match_priority"] = (
                    title_hit[mask].astype(int) * 2 + skill_hit[mask].astype(int)
                )
                filtered = filtered.sort_values("_match_priority", ascending=False)
                filtered = filtered.drop(columns=["_match_priority"])
                applied.append("skills")
            else:
                return self._no_match_jobs(parsed, top_n, user_name, "skills")

        if parsed["location"]:
            loc = LOCATION_ALIASES.get(parsed["location"], parsed["location"]).lower()
            mask = filtered["job_location"].str.lower().str.contains(loc, na=False)
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("location")
            else:
                return self._no_match_jobs(parsed, top_n, user_name, "location")

        if parsed["job_type"]:
            mask = filtered["job_type"].str.lower().str.contains(
                parsed["job_type"].lower(), na=False)
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("job_type")
            else:
                return self._no_match_jobs(parsed, top_n, user_name, "job_type")

        # If the user gave criteria but NONE were recognized, be honest
        # instead of dumping random top-ranked jobs.
        raw_msg = parsed.get("raw", "")
        msg_has_criteria = bool(re.search(
            r"\b(java|python|flutter|react|node|php|laravel|django|swift|kotlin|"
            r"angular|vue|go|rust|ruby|cobol|fortran|scala|typescript|dotnet|"
            r"backend|frontend|mobile|data|ai|ml|cloud|devops|security)\b",
            raw_msg.lower()
        ))
        # If user phrased it like a real query but we matched nothing, refuse to guess.
        if not applied and (msg_has_criteria or len(raw_msg.split()) >= 3):
            return {
                "intent" : "job_search",
                "reply"  : f"{greeting}مش فاهم التخصص أو السكيل اللي عايزه بالظبط 😅 "
                           f"جرب تقولي مثلاً: 'python remote' أو 'flutter cairo'.",
                "type"   : "jobs", "count": 0, "results": [],
                "follow_up": "ايه التخصص أو السكيل؟",
            }

        # Personalized ranking: keep results strictly inside `filtered`.
        # When the user named a specific skill, trust the title-priority sort
        # over personalization (otherwise "node.js" can surface "Python Developer").
        results = filtered.head(top_n)
        if user_id and "skills" not in applied:
            u = self.users[self.users["user_id"] == user_id]
            if not u.empty:
                try:
                    ranked = self.engine.recommend(u.iloc[0], filtered, top_n=top_n)
                    allowed_ids = set(filtered["job_id"].tolist())
                    ranked = ranked[ranked["job_id"].isin(allowed_ids)]
                    if not ranked.empty:
                        results = ranked.head(top_n)
                except Exception:
                    pass

        count = len(results)
        if count == 0:
            return self._fallback_to_courses(parsed, top_n, user_name)

        follow_up = None
        if "location" not in applied and "job_type" not in applied:
            follow_up = MISSING_INFO_FOLLOWUP["job_search"]

        # Reply text mirrors only filters that were actually applied
        skills_s = ", ".join(parsed["skills"]) if "skills"  in applied else ""
        loc_s    = f" في {parsed['location']}" if "location" in applied else ""
        type_s   = f" ({parsed['job_type']})"  if "job_type" in applied else ""

        return {
            "intent"    : "job_search",
            "reply"     : f"{greeting}لقيتلك {count} وظيفة{' ' + skills_s if skills_s else ''}{loc_s}{type_s}! 🎯",
            "type"      : "jobs",
            "count"     : count,
            "results"   : _fmt_jobs(results),
            "follow_up" : follow_up,
        }

    def _no_match_jobs(self, parsed, top_n, user_name, missing_field):
        greeting = f"{user_name}، " if user_name else ""
        wanted = []
        if parsed["skills"]:   wanted.append(", ".join(parsed["skills"]))
        if parsed["location"]: wanted.append(parsed["location"])
        if parsed["job_type"]: wanted.append(parsed["job_type"])
        criteria = " / ".join(wanted) if wanted else "اللي طلبته"
        return {
            "intent"    : "job_search",
            "reply"     : f"{greeting}مش لاقي أي وظيفة بـ ({criteria}) في الـ dataset حالياً 😕",
            "type"      : "jobs",
            "count"     : 0,
            "results"   : [],
            "follow_up" : "تحب أوريك كورسات تأهلك للمجال ده؟",
        }

    # ── Course Search ─────────────────────────────────────────
    def _handle_course_search(self, parsed, top_n, user_name, context):
        filtered = self.courses.copy()
        greeting = f"{user_name}، " if user_name else ""
        applied  = []

        specialty = parsed["specialty"]
        if not specialty and context:
            for prev in reversed(context):
                if isinstance(prev, dict) and prev.get("specialty"):
                    specialty = prev["specialty"]
                    break

        if specialty:
            mask = filtered["specialty"].str.lower() == specialty.lower()
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("specialty")

        if parsed["skills"]:
            mask = filtered["skills"].apply(
                lambda x: _any_token_match(x, parsed["skills"]))
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("skills")
            else:
                return self._no_match_courses(parsed, user_name, "skills",
                                              ", ".join(parsed["skills"]))

        if parsed["level"]:
            mask = filtered["level"].str.lower() == parsed["level"].lower()
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("level")
            else:
                return self._no_match_courses(parsed, user_name, "level", parsed["level"])

        if parsed["language"]:
            mask = filtered["language"] == parsed["language"]
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("language")
            else:
                return self._no_match_courses(parsed, user_name, "language", parsed["language"])

        if parsed["free"]:
            mask = filtered["price"].str.lower().isin(["free", "مجاني"])
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("free")
            else:
                return self._no_match_courses(parsed, user_name, "free", "مجانية")

        results = filtered.sort_values("rating", ascending=False).head(top_n)
        count   = len(results)

        if count == 0:
            return self._fallback_to_jobs(parsed, top_n, user_name)

        follow_up = None if "level" in applied else MISSING_INFO_FOLLOWUP["course_search"]

        topic_parts = []
        if "specialty" in applied: topic_parts.append(specialty)
        elif "skills" in applied:  topic_parts.append(", ".join(parsed["skills"]))
        topic   = " ".join(topic_parts)
        level_s = f" {parsed['level']}" if "level" in applied else ""
        lang_s  = " بالعربي" if "language" in applied and parsed["language"] == "Arabic" else ""
        free_s  = " مجانية" if "free" in applied else ""

        return {
            "intent"    : "course_search",
            "reply"     : f"{greeting}لقيتلك {count} كورس{' ' + topic if topic else ''}{level_s}{lang_s}{free_s}! 📚",
            "type"      : "courses",
            "specialty" : specialty,
            "count"     : count,
            "results"   : _fmt_courses(results.to_dict(orient="records")),
            "follow_up" : follow_up,
        }

    def _no_match_courses(self, parsed, user_name, field, value):
        greeting = f"{user_name}، " if user_name else ""
        return {
            "intent"    : "course_search",
            "reply"     : f"{greeting}مش لاقي كورسات بالمواصفات دي ({value}) 😕",
            "type"      : "courses",
            "count"     : 0,
            "results"   : [],
            "follow_up" : "جرب تخفف الفلاتر أو تخصص تاني؟",
        }

    # ── Fallbacks ─────────────────────────────────────────────
    def _fallback_to_courses(self, parsed, top_n, user_name):
        greeting = f"{user_name}، " if user_name else ""
        filtered = self.courses.copy()
        if parsed["specialty"]:
            mask = filtered["specialty"].str.lower() == parsed["specialty"].lower()
            if mask.sum() > 0: filtered = filtered[mask]
            else: filtered = filtered.iloc[0:0]
        elif parsed["skills"]:
            mask = filtered["skills"].apply(lambda x: _any_token_match(x, parsed["skills"]))
            if mask.sum() > 0: filtered = filtered[mask]
            else: filtered = filtered.iloc[0:0]
        results = filtered.sort_values("rating", ascending=False).head(top_n) if not filtered.empty else filtered
        if results.empty:
            return {
                "intent": "fallback_courses",
                "reply" : f"{greeting}مش لاقي وظايف ولا كورسات بالمواصفات دي 😕",
                "type"  : "text", "count": 0, "results": [],
                "follow_up": "جرب تخصص تاني أو سكيلز مختلفة؟",
            }
        return {
            "intent"    : "fallback_courses",
            "reply"     : f"{greeting}مش لاقي وظايف بالمواصفات دي دلوقتي 😕\nبس لقيتلك {len(results)} كورس يقويك للوظيفة الجاية! 📚",
            "type"      : "courses",
            "count"     : len(results),
            "results"   : _fmt_courses(results.to_dict(orient="records")),
            "follow_up" : "عايز تشوف وظايف في تخصص تاني؟",
        }

    def _fallback_to_jobs(self, parsed, top_n, user_name):
        greeting = f"{user_name}، " if user_name else ""
        filtered = self.jobs.copy()
        if parsed["specialty"]:
            mask = filtered["industry"].str.lower() == parsed["specialty"].lower()
            if mask.sum() > 0: filtered = filtered[mask]
            else: filtered = filtered.iloc[0:0]
        elif parsed["skills"]:
            mask = filtered["job_required_skills"].apply(lambda x: _any_token_match(x, parsed["skills"]))
            if mask.sum() > 0: filtered = filtered[mask]
            else: filtered = filtered.iloc[0:0]
        results = filtered.head(top_n)
        if results.empty:
            return {
                "intent": "fallback_jobs",
                "reply" : f"{greeting}مش لاقي كورسات ولا وظايف بالمواصفات دي 😕",
                "type"  : "text", "count": 0, "results": [],
                "follow_up": "جرب فلاتر مختلفة؟",
            }
        return {
            "intent"    : "fallback_jobs",
            "reply"     : f"{greeting}مش لاقي كورسات بالمواصفات دي 😕\nبس لقيتلك {len(results)} وظيفة في نفس المجال! 💼",
            "type"      : "jobs",
            "count"     : len(results),
            "results"   : _fmt_jobs(results),
            "follow_up" : "عايز تغير الفلاتر؟",
        }

    # ── Company Search ────────────────────────────────────────
    def _handle_company_search(self, parsed, top_n):
        filtered = self.users.copy()
        applied  = []

        if parsed["skills"]:
            mask = filtered["user_skills"].apply(lambda x: _any_token_match(x, parsed["skills"]))
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("skills")
            else:
                return {
                    "intent": "company_search",
                    "reply" : f"مش لاقي مرشحين بسكيلز ({', '.join(parsed['skills'])}) 😕",
                    "type"  : "candidates", "count": 0, "results": [], "follow_up": None,
                }

        if parsed["location"]:
            mask = filtered["user_location"].str.lower().str.contains(
                parsed["location"].lower(), na=False)
            if mask.sum() > 0:
                filtered = filtered[mask]
                applied.append("location")
            else:
                return {
                    "intent": "company_search",
                    "reply" : f"مش لاقي مرشحين في ({parsed['location']}) 😕",
                    "type"  : "candidates", "count": 0, "results": [], "follow_up": None,
                }

        results  = filtered[["user_id","user_name","role","user_skills",
                              "user_location","experience_years","expected_salary_egp"]
                            ].drop_duplicates("user_id").head(top_n)
        skills_s = ", ".join(parsed["skills"]) if "skills" in applied else ""
        return {
            "intent"    : "company_search",
            "reply"     : (f"لقيتلك {len(results)} مرشح{' بسكيلز ' + skills_s if skills_s else ''}! 👤"
                           if len(results) > 0 else "مش لاقي مرشحين. جرب تغير الفلاتر!"),
            "type"      : "candidates",
            "count"     : len(results),
            "results"   : results.to_dict(orient="records"),
            "follow_up" : None,
        }

    # ── CV Help ───────────────────────────────────────────────
    def _reply_cv_help(self, user_name):
        greeting = f"{user_name}، " if user_name else ""
        tips = [
            "اكتب ملخص قصير عن نفسك في أول الـ CV (3-4 جمل بس).",
            "حط السكيلز التقنية بتاعتك بوضوح زي: Python | Flutter | Firebase.",
            "اذكر مشاريعك مع لينكات GitHub لو موجودة.",
            "ابدأ كل نقطة في الـ Experience بفعل: طورت، بنيت، حسنت.",
            "خلي الـ CV صفحة واحدة لو خبرتك أقل من 3 سنين.",
            "حط بياناتك كاملة: إيميل، LinkedIn، GitHub، رقم تليفون.",
        ]
        return {
            "intent"    : "cv_help",
            "reply"     : f"{greeting}إليك أهم نصائح الـ CV! 📄",
            "type"      : "tips",
            "count"     : len(tips),
            "results"   : [{"tip": t} for t in tips],
            "follow_up" : "عايز نراجع الـ CV بتاعك؟ ابعت ملف الـ PDF.",
        }

    # ── Greeting ──────────────────────────────────────────────
    def _reply_greeting(self, user_name):
        greeting = f"أهلاً {user_name}! " if user_name else "أهلاً! "
        return {
            "intent"    : "greeting",
            "reply"     : (f"{greeting}أنا JobNest AI 🤖 كيف أساعدك؟\n\n"
                           "- وظايف: 'Find me flutter jobs'\n"
                           "- كورسات: 'Recommend Python courses'\n"
                           "- مسار: 'AI track' أو 'Flutter roadmap'\n"
                           "- هدف: 'I want to freelance'\n"
                           "- معلومات: 'What is machine learning?'\n"
                           "- CV: 'CV tips'"),
            "type"      : "text", "count": 0, "results": [], "follow_up": None,
        }

    # ── Unknown ───────────────────────────────────────────────
    def _reply_unknown(self):
        return {
            "intent"    : "unknown",
            "reply"     : "مش فاهم قصدك 😅 جرب مثلاً:",
            "type"      : "suggestions",
            "count"     : 6,
            "results"   : [
                {"example": "Find me remote Flutter jobs"},
                {"example": "Recommend beginner Python courses"},
                {"example": "I want a data science track"},
                {"example": "What is machine learning?"},
                {"example": "What skills do I need for AI?"},
                {"example": "CV tips"},
            ],
            "follow_up" : None,
        }


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────

def _any_token_match(field_value, wanted_skills) -> bool:
    """Whole-token match against a pipe/comma-delimited skills field.
    'java' won't match 'JavaScript', but 'node' WILL match 'Node.js'.
    """
    if not wanted_skills or field_value is None:
        return False
    if pd.isna(field_value):
        return False
    text = str(field_value).lower()
    # split on common delimiters; keep '.' and '+' inside tokens (node.js, c++)
    tokens = set(re.split(r"[|,;/\s]+", text))
    tokens = {t.strip() for t in tokens if t.strip()}
    for sk in wanted_skills:
        sk = sk.lower().strip()
        if not sk:
            continue
        if sk in tokens:
            return True
        # Tolerate 'node' matching 'node.js', 'next' matching 'next.js', etc.
        for tok in tokens:
            if tok == sk or tok.startswith(sk + ".") or tok.startswith(sk + "+"):
                return True
    return False


def _fmt_jobs(df) -> list:
    records = df.to_dict(orient="records") if isinstance(df, pd.DataFrame) else df
    cols = {"job_id","title","company_name","industry","job_type","job_location",
            "salary_range_egp","experience_required","job_required_skills",
            "content_score","ml_score","final_score"}
    return [{k: (float(v) if hasattr(v,"item") else v)
             for k,v in r.items() if k in cols} for r in records]


def _fmt_courses(records) -> list:
    if isinstance(records, pd.DataFrame):
        records = records.to_dict(orient="records")
    cols = {"course_id","title","platform","instructor","specialty","skills",
            "level","duration","price","rating","language","certificate","url"}
    return [{k: (float(v) if hasattr(v,"item") else v)
             for k,v in r.items() if k in cols} for r in records]
