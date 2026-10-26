import os
import json
import random
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from app.config import BACKEND_DIR, ENV_PATH

logger = logging.getLogger("question_service")
logger.setLevel(logging.INFO)

# Comprehensive progressive scenario question repository for all 10 supported programming languages
# in both English and Tamil. Every language has authentic, high-caliber technical scenarios.
QUESTION_BANKS: Dict[str, Dict[str, List[Dict[str, Any]]]] = {
    "Python": {
        "English": [
            {
                "id": 1,
                "title": "Data Pipeline Memory Optimization with Generators",
                "question": "You are building a Python microservice that parses a 15-gigabyte server access log on an instance with only 4 gigabytes of memory. Loading the lines into a standard list raises a MemoryError. How would you architect this file processing pipeline using Python generator expressions and lazy evaluation so that lines are streamed sequentially with minimal memory footprint?",
                "difficulty": "Easy-Medium",
                "concept": "Generators & Memory Optimization"
            },
            {
                "id": 2,
                "title": "API Rate Limiting with Higher-Order Decorators",
                "question": "Your backend team needs to protect a downstream third-party REST API client from exceeding 60 requests per minute across concurrent worker threads. How would you design and implement a custom Python decorator using functools and sliding window time-tracking to enforce this rate limit?",
                "difficulty": "Medium",
                "concept": "Decorators & Concurrency"
            },
            {
                "id": 3,
                "title": "Debugging Mutable Default Arguments in Production",
                "question": "A production bug report reveals that items added by one customer occasionally appear in the shopping carts of other concurrent users. The function signature is `def add_item(item, cart=[])`. Explain why this happens within Python's function definition scoping model and how you would refactor it.",
                "difficulty": "Medium",
                "concept": "Scoping & Mutable Defaults"
            },
            {
                "id": 4,
                "title": "AsyncIO vs Multiprocessing under the Global Interpreter Lock (GIL)",
                "question": "You need to build a system that fetches product metadata from 5,000 external HTTP endpoints and computes SHA-256 hashes of the downloaded product images. Given Python's Global Interpreter Lock (GIL), how would you split this workload between AsyncIO for I/O-bound networking and Multiprocessing for CPU-bound hashing?",
                "difficulty": "Medium-Hard",
                "concept": "AsyncIO, GIL & Multiprocessing"
            },
            {
                "id": 5,
                "title": "Preventing Deadlocks in Multi-Threaded Financial Transactions",
                "question": "In a multithreaded Python banking microservice, concurrent fund transfers between matching accounts occasionally trigger deadlocks where threads freeze indefinitely. What causes this deadlock, and how would you implement a resource-ordering lock hierarchy or atomic transaction pattern to prevent it?",
                "difficulty": "Hard",
                "concept": "Thread Safety & Lock Hierarchies"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "பைதான் ஜெனரேட்டர்கள் மூலம் நினைவக உகப்பாக்கம்",
                "question": "4 ஜிபி ரேம் மட்டுமே உள்ள சர்வரில் 15 ஜிபி பதிவு கோப்பை (log file) வாசிக்கும் போது MemoryError ஏற்படுகிறது. கணினி நினைவகம் வீணாகாமல் இருக்க பைதான் ஜெனரேட்டர்கள் (generators) மற்றும் லேஸி எவாலுவேஷன் (lazy evaluation) கொண்டு இதனை எவ்வாறு வடிவமைப்பீர்கள்?",
                "difficulty": "Easy-Medium",
                "concept": "ஜெனரேட்டர்கள் மற்றும் மெமரி மேலாண்மை"
            },
            {
                "id": 2,
                "title": "API அழைப்புகளை கட்டுப்படுத்தும் டெக்கரேட்டர்கள்",
                "question": "ஒரு நிமிடத்திற்கு 60 API அழைப்புகளுக்கு மேல் செல்லாதவாறு உங்கள் பைதான் சர்வீஸை கட்டுப்படுத்த வேண்டும். இதற்கு functools பயன்படுத்தி ஒரு தனிப்பயன் டெக்கரேட்டரை (custom decorator) எவ்வாறு உருவாக்குவீர்கள்?",
                "difficulty": "Medium",
                "concept": "பைதான் டெக்கரேட்டர்கள்"
            },
            {
                "id": 3,
                "title": "மாறும் இயல்புநிலை அளவுரு பிழைத்திருத்தம்",
                "question": "ஷாப்பிங் கார்ட் அப்ளிகேஷனில் `def add_item(item, cart=[])` என எழுதப்பட்டதால் ஒரு பயனரின் பொருட்கள் மற்றவருக்கும் தெரிகிறது. பைதானில் இந்த பிழை ஏன் ஏற்படுகிறது? இதை எவ்வாறு சரிசெய்வீர்கள்?",
                "difficulty": "Medium",
                "concept": "Python Scoping & Mutable Defaults"
            },
            {
                "id": 4,
                "title": "AsyncIO மற்றும் Multiprocessing கட்டிடக்கலை",
                "question": "5,000 இணையதளங்களில் இருந்து தகவல்களை பதிவிறக்கம் செய்து படங்களை ஹாஷ் செய்ய வேண்டும். பைதான் GIL கட்டுப்பாட்டை கருத்தில் கொண்டு, I/O வேலைகளுக்கு AsyncIO மற்றும் CPU வேலைகளுக்கு Multiprocessing எவ்வாறு பிரித்து அமைப்பீர்கள்?",
                "difficulty": "Medium-Hard",
                "concept": "AsyncIO, GIL & Multiprocessing"
            },
            {
                "id": 5,
                "title": "வங்கி பரிவர்த்தனைகளில் டெட்லாக் தவிர்த்தல்",
                "question": "ஒரே கணக்குகளுக்கு இடையே ஒரே நேரத்தில் பணம் மாற்றப்படும்போது த்ரெட்கள் முடங்கி (deadlock) சர்வர் நிற்கிறது. இந்த டெட்லாக்கை தவிர்க்க உங்கள் லாக் வரிசைப்படுத்துதல் உத்தி என்ன?",
                "difficulty": "Hard",
                "concept": "த்ரெட் பாதுகாப்பு & கன்கரன்சி"
            }
        ]
    },
    "Java": {
        "English": [
            {
                "id": 1,
                "title": "JVM Garbage Collection Pause Reduction",
                "question": "A mission-critical Java payment gateway processing 10,000 transactions per second experiences periodic 2-second stop-the-world garbage collection pauses. How would you analyze GC logs, tune JVM heap generations, and transition to G1GC or ZGC to keep pauses below 10 milliseconds?",
                "difficulty": "Easy-Medium",
                "concept": "JVM Memory Tuning & GC Algorithms"
            },
            {
                "id": 2,
                "title": "ThreadPoolExecutor Configuration and Rejection Policies",
                "question": "During flash sales, a Spring Boot application crashes with 'OutOfMemoryError: unable to create new native thread'. How would you properly size core and maximum pool sizes, choose between bounded ArrayBlockingQueue and SynchronousQueue, and handle rejected tasks gracefully?",
                "difficulty": "Medium",
                "concept": "ThreadPoolExecutor & Concurrency"
            },
            {
                "id": 3,
                "title": "Atomicity and Thread Safety in ConcurrentHashMap",
                "question": "A developer writes `if (!cache.containsKey(key)) { cache.put(key, fetchFromDB()); }` inside a multi-threaded service and discovers duplicate database queries under load. Why is this composite operation not thread-safe despite ConcurrentHashMap, and how does `computeIfAbsent()` provide atomicity?",
                "difficulty": "Medium",
                "concept": "ConcurrentHashMap & Atomic Operations"
            },
            {
                "id": 4,
                "title": "Preventing Deadlocks in Spring Data JPA Database Transactions",
                "question": "Under high concurrent checkout volume, inventory reservation updates trigger SQL serialization deadlocks in PostgreSQL. How would you structure JPA transactions, select between Optimistic with versioning and Pessimistic Write locks, and implement exponential backoff retries?",
                "difficulty": "Medium-Hard",
                "concept": "JPA Locking & Transaction Isolation"
            },
            {
                "id": 5,
                "title": "Java 21 Virtual Threads (Project Loom) Migration & Thread Pinning",
                "question": "Your engineering team is migrating a high-throughput microservice from platform threads to Java 21 Virtual Threads. What causes thread pinning when virtual threads execute `synchronized` blocks or native methods, and how do you refactor with `ReentrantLock`?",
                "difficulty": "Hard",
                "concept": "Virtual Threads & Carrier Thread Pinning"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "JVM கார்பேஜ் கலெக்ஷன் தாமதங்களை குறைத்தல்",
                "question": "அதிக பரிவர்த்தனைகள் நடக்கும் ஜாவா அப்ளிகேஷனில் அடிக்கடி 2 வினாடிகள் GC இடைநிறுத்தங்கள் (stop-the-world pauses) ஏற்படுகின்றன. இதனை மில்லி விநாடிகளாக குறைக்க G1GC அல்லது ZGC அமைப்புகளை எவ்வாறு மாற்றுவீர்கள்?",
                "difficulty": "Easy-Medium",
                "concept": "JVM Memory & Garbage Collection"
            },
            {
                "id": 2,
                "title": "திரெட் பூல் மற்றும் அவுட் ஆஃப் மெமரி தடுப்பு",
                "question": "அதிக நெரிசலின் போது 'unable to create new native thread' என்ற பிழையுடன் ஜாவா சர்வர் முடங்குகிறது. ThreadPoolExecutor-ல் சரியான திரெட் அளவு, Queue மற்றும் Rejection Policy-ஐ எவ்வாறு கட்டமைப்பீர்கள்?",
                "difficulty": "Medium",
                "concept": "ThreadPoolExecutor"
            },
            {
                "id": 3,
                "title": "ConcurrentHashMap அணுத்தன்மை மற்றும் ரேஸ் கண்டிஷன்",
                "question": "ConcurrentHashMap பயன்படுத்திய பிறகும் `containsKey` மற்றும் `put` செயல்பாடுகள் தனித்தனியாக உள்ளதால் டூப்ளிகேட் அழைப்புகள் ஏற்படுகின்றன. `computeIfAbsent` மூலம் இந்த அணுத்தன்மையை எவ்வாறு உறுதி செய்வீர்கள்?",
                "difficulty": "Medium",
                "concept": "Concurrent Collections & Atomicity"
            },
            {
                "id": 4,
                "title": "Spring JPA டேட்டாபேஸ் பரிவர்த்தனை மற்றும் பூட்டுகள்",
                "question": "பொருட்களை ஒரே நேரத்தில் பலர் வாங்கும்போது டேட்டாபேஸில் Deadlock ஏற்படுகிறது. Spring JPA-வில் Optimistic மற்றும் Pessimistic லாக் மற்றும் ரீட்ரை லாஜிக்கை எவ்வாறு அமைப்பீர்கள்?",
                "difficulty": "Medium-Hard",
                "concept": "Database Transactions & Locking"
            },
            {
                "id": 5,
                "title": "ஜாவா 21 விர்ச்சுவல் திரெட்கள் மற்றும் Thread Pinning",
                "question": "ஜாவா 21 விர்ச்சுவல் திரெட்களுக்கு மாறும்போது 'Thread Pinning' பிரச்சனை எப்போது ஏற்படுகிறது? synchronized blocks-ஐ ReentrantLock கொண்டு மாற்றுவதன் அவசியம் என்ன?",
                "difficulty": "Hard",
                "concept": "Virtual Threads & Project Loom"
            }
        ]
    },
    "JavaScript": {
        "English": [
            {
                "id": 1,
                "title": "Event Loop Microtask Queue Starvation",
                "question": "A Node.js/browser dashboard freezes completely when processing high-frequency WebSocket messages scheduled via continuous `Promise.resolve().then()`. Explain the difference between macrotasks and microtasks in the JavaScript Event Loop, why the UI rendering is starved, and how you would balance execution.",
                "difficulty": "Easy-Medium",
                "concept": "Event Loop & Task Queues"
            },
            {
                "id": 2,
                "title": "Diagnosing Closures and Memory Leaks in Single-Page Apps",
                "question": "A React/Vue Single Page Application consumes steadily increasing RAM over hours of usage. You suspect event listeners attached to the window and closures referencing unmounted DOM elements are preventing garbage collection. How would you identify and eliminate these leaks using Chrome DevTools Heap Snapshots?",
                "difficulty": "Medium",
                "concept": "Closures & Garbage Collection"
            },
            {
                "id": 3,
                "title": "Custom Debounce and Throttle Implementation with Cancellation",
                "question": "How would you build a production-ready debounce utility from scratch that supports trailing/leading edge execution, cancellation, and preserves the original function's `this` context and arguments?",
                "difficulty": "Medium",
                "concept": "Higher-Order Functions & Timing"
            },
            {
                "id": 4,
                "title": "Handling Async Network Race Conditions with AbortController",
                "question": "In an autocomplete search field, when a user types rapidly, an earlier slow request sometimes resolves after a newer fast request, overwriting the UI with outdated results. How do you implement `AbortController` in vanilla JavaScript/Fetch to cancel stale in-flight requests?",
                "difficulty": "Medium-Hard",
                "concept": "Async State & AbortController"
            },
            {
                "id": 5,
                "title": "High-Throughput DOM Rendering and Virtualization",
                "question": "Your application receives 5,000 real-time stock price updates per second. Directly manipulating the DOM drops frame rates to 5 FPS. How would you architect a virtualized windowing table and batch DOM updates using `requestAnimationFrame` to maintain smooth 60 FPS performance?",
                "difficulty": "Hard",
                "concept": "DOM Virtualization & Batching"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "ஜாவாஸ்கிரிப்ட் ஈவென்ட் லூப் மற்றும் மைக்ரோடாஸ்க் சிக்கல்",
                "question": "வெப் சாக்கெட் வழியாக அதிக தரவு வரும்போது UI இடைமுகம் முடங்குகிறது. JavaScript Event Loop-ல் Macrotask மற்றும் Microtask இடையே உள்ள வேறுபாடு என்ன? UI ரெண்டரிங் பாதிக்கப்படாமல் இருக்க என்ன செய்வீர்கள்?",
                "difficulty": "Easy-Medium",
                "concept": "Event Loop & Tasks"
            },
            {
                "id": 2,
                "title": "மெமரி கசிவு (Memory Leak) கண்டறிதல்",
                "question": "ஒரு Single Page அப்ளிகேஷனில் நேரம் செல்ல செல்ல மெமரி பயன்பாடு அதிகரித்துக்கொண்டே செல்கிறது. DOM ஈவென்ட் லிசனர்ஸ் மற்றும் குளோஷர்ஸ் (closures) மூலம் ஏற்படும் மெமரி கசிவை எவ்வாறு சரிசெய்வீர்கள்?",
                "difficulty": "Medium",
                "concept": "Closures & Memory"
            },
            {
                "id": 3,
                "title": "தேடல் உள்ளீட்டுக்கு Debounce உத்தி",
                "question": "தொடர்ச்சியான பயனர் உள்ளீடுகளுக்கு ஒரு தனிப்பயன் debounce மற்றும் throttle செயற்கூறை எவ்வாறு உருவாக்குவீர்கள்? `this` context எவ்வாறு பாதுகாக்கப்படுகிறது?",
                "difficulty": "Medium",
                "concept": "Higher-Order Functions"
            },
            {
                "id": 4,
                "title": "AbortController மூலம் பழைய அழைப்புகளை ரத்து செய்தல்",
                "question": "பயனர் வேகமாக தேடும் போது பழைய API பதில்கள் புதிய பதில்களுக்குப் பிறகு வந்து சேர்வதால் தவறான தகவல்கள் காட்டப்படுகின்றன. AbortController பயன்படுத்தி முந்தைய நெட்வொர்க் அழைப்புகளை எவ்வாறு ரத்து செய்வீர்கள்?",
                "difficulty": "Medium-Hard",
                "concept": "AbortController & Async State"
            },
            {
                "id": 5,
                "title": "விர்ச்சுவல் லிஸ்ட் மூலம் 60 FPS செயல்திறன்",
                "question": "வினாடிக்கு 5,000 பங்குச்சந்தை புதுப்பிப்புகள் வரும்போது UI ஃபிரேம்கள் குறைகின்றன. இந்த இடைமுகத்தை மென்மையாக 60 FPS வேகத்தில் இயக்க விர்ச்சுவல் லிஸ்ட் (virtualized list) மற்றும் requestAnimationFrame-ஐ எவ்வாறு பயன்படுத்துவீர்கள்?",
                "difficulty": "Hard",
                "concept": "Virtualization & Performance"
            }
        ]
    },
    "TypeScript": {
        "English": [
            {
                "id": 1,
                "title": "Discriminated Unions and Type Narrowing in State Management",
                "question": "You are modeling network request states in TypeScript. Using optional fields like `{ loading?: boolean, data?: Data, error?: Error }` causes runtime bugs where `error` and `data` coexist. How would you redesign this using Discriminated Unions and exhaustive type checking with the `never` type?",
                "difficulty": "Easy-Medium",
                "concept": "Discriminated Unions & Exhaustiveness"
            },
            {
                "id": 2,
                "title": "Advanced Generic Constraints and Conditional Types",
                "question": "Design a type-safe API routing map in TypeScript where entering an endpoint path like `'/api/users/:id'` automatically extracts route parameters into a strongly-typed params object `{ id: string }` using recursive template literal types and conditional inference with `infer`.",
                "difficulty": "Medium",
                "concept": "Template Literal Types & infer"
            },
            {
                "id": 3,
                "title": "Strict Null Checks and Deep Readonly Immutability",
                "question": "In a critical state management store, nested state objects are accidentally being mutated in place. How would you construct a recursive `DeepReadonly<T>` type utility in TypeScript to enforce compile-time immutability across arbitrarily nested structures?",
                "difficulty": "Medium",
                "concept": "Recursive Mapped Types"
            },
            {
                "id": 4,
                "title": "Type-Safe Event Emitter with Generic Callbacks",
                "question": "Implement a fully type-safe EventEmitter class where subscribing to specific events (e.g. `'userLogin'`, `'orderCreated'`) strictly enforces the payload argument types based on a provided event interface map.",
                "difficulty": "Medium-Hard",
                "concept": "Generic Interfaces & Keyof Constraints"
            },
            {
                "id": 5,
                "title": "TypeScript Declaration Files and Library Typing",
                "question": "Your company is wrapping an untyped legacy JavaScript library that dynamically binds methods to prototypes at runtime. How would you author a `.d.ts` declaration file utilizing declaration merging, module augmentation, and ambient namespaces without changing the runtime code?",
                "difficulty": "Hard",
                "concept": "Declaration Merging & Ambient Modules"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "டைப்ஸ்கிரிப்ட் Discriminated Unions மற்றும் ஸ்டேட் மேலாண்மை",
                "question": "நெட்வொர்க் அழைப்புகளில் லோடிங், டேட்டா, எரர் ஆகியவற்றை தனித்தனி விருப்பங்களாக வைக்கும் போது பிழைகள் வருகின்றன. Discriminated Unions மற்றும் never டைப் பயன்படுத்தி இந்த ஸ்டேட்களை எவ்வாறு பாதுகாப்பாக வடிவமைப்பீர்கள்?",
                "difficulty": "Easy-Medium",
                "concept": "Discriminated Unions"
            },
            {
                "id": 2,
                "title": "Conditional Types மற்றும் Template Literal Types",
                "question": "ஒரு API URL பாதையிலிருந்து (`/users/:id`) அளவுருக்களை (parameters) தானாக பிரித்து ஸ்ட்ராங்லி-டைப்ட் (strongly typed) ஆப்ஜெக்ட்டாக மாற்றும் டைப்ஸ்கிரிப்ட் வகையை `infer` கொண்டு எவ்வாறு உருவாக்குவீர்கள்?",
                "difficulty": "Medium",
                "concept": "Conditional Types & infer"
            },
            {
                "id": 3,
                "title": "DeepReadonly மூலம் இம்முயூட்டபிலிட்டி உறுதி செய்தல்",
                "question": "நெஸ்டட் ஆப்ஜெக்ட்கள் தற்செயலாக மாற்றப்படுவதை தடுக்க, கம்பைல்-டைமில் எந்த ஒரு நெஸ்டட் அளவிலும் மாற்ற முடியாதவாறு ஒரு `DeepReadonly<T>` யூட்டிலிட்டியை எவ்வாறு உருவாக்குவீர்கள்?",
                "difficulty": "Medium",
                "concept": "Mapped Types"
            },
            {
                "id": 4,
                "title": "டைப்-பாதுகாப்பான Event Emitter உருவாக்குதல்",
                "question": "வெவ்வேறு நிகழ்வுகளுக்கு (events) அதற்கேற்ற சரியான டேட்டாவை மட்டுமே அனுப்பும் வகையிலான டைப்-பாதுகாப்பான Generic EventEmitter வகுப்பை எவ்வாறு வடிவமைப்பீர்கள்?",
                "difficulty": "Medium-Hard",
                "concept": "Generics & Keyof"
            },
            {
                "id": 5,
                "title": "Declaration Merging மற்றும் ambient types",
                "question": "பழைய ஜாவாஸ்கிரிப்ட் லைப்ரரிக்கு ஒரு `.d.ts` டெக்ளரேஷன் கோப்பை உருவாக்கும் போது, Declaration Merging மற்றும் Module Augmentation-ஐ எவ்வாறு கையாள்வீர்கள்?",
                "difficulty": "Hard",
                "concept": "Declaration Merging"
            }
        ]
    },
    "C++": {
        "English": [
            {
                "id": 1,
                "title": "RAII and Smart Pointer Selection in High-Performance Systems",
                "question": "In a high-frequency trading application written in modern C++, memory leaks and dangling pointers cause unpredictable crashes. Contrast `std::unique_ptr`, `std::shared_ptr`, and `std::weak_ptr` regarding atomic reference counting overhead, cyclic dependencies, and custom deleters under the RAII principle.",
                "difficulty": "Easy-Medium",
                "concept": "RAII & Smart Pointers"
            },
            {
                "id": 2,
                "title": "Move Semantics, Rvalue References, and Perfect Forwarding",
                "question": "Explain how move constructors and `std::move` eliminate deep heap copies when manipulating dynamic arrays or strings. How does `std::forward` combined with universal references (`T&&`) resolve the perfect forwarding problem in factory template functions?",
                "difficulty": "Medium",
                "concept": "Move Semantics & std::forward"
            },
            {
                "id": 3,
                "title": "Memory Layout, Cache Lines, and False Sharing",
                "question": "A multi-threaded C++ engine runs slower on 16 CPU cores than on 2 cores. Profiling shows intense cache invalidation on adjacent struct variables accessed by different threads. Explain False Sharing and how you would apply `alignas(64)` and hardware cache line padding to resolve it.",
                "difficulty": "Medium",
                "concept": "Memory Alignment & Cache Coherence"
            },
            {
                "id": 4,
                "title": "Lock-Free Programming with std::atomic and Memory Models",
                "question": "In a low-latency audio processing pipeline where mutex locks cause priority inversion audio glitches, how would you implement a lock-free single-producer single-consumer ring buffer using `std::atomic` and fine-grained `memory_order_acquire` and `memory_order_release`?",
                "difficulty": "Medium-Hard",
                "concept": "Lock-Free Concurrency & Memory Orders"
            },
            {
                "id": 5,
                "title": "Template Metaprogramming and C++20 Concepts",
                "question": "Legacy C++ codebases heavily rely on complex SFINAE with `std::enable_if` to constrain template overloads, producing indecipherable compiler errors. How do C++20 Concepts and `requires` clauses simplify compile-time constraints and improve compile diagnostics?",
                "difficulty": "Hard",
                "concept": "C++20 Concepts & SFINAE"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "C++ RAII மற்றும் ஸ்மார்ட் பாயிண்டர்கள்",
                "question": "நினைவக கசிவை (memory leak) தடுக்க C++ மொழியில் `std::unique_ptr` மற்றும் `std::shared_ptr` எப்போது எவ்வாறு பயன்படுத்த வேண்டும்? Circular reference சிக்கலை `std::weak_ptr` கொண்டு எவ்வாறு தீர்ப்பீர்கள்?",
                "difficulty": "Easy-Medium",
                "concept": "RAII & Smart Pointers"
            },
            {
                "id": 2,
                "title": "மூவ் செமண்டிக்ஸ் மற்றும் பெர்ஃபெக்ட் பார்வர்டிங்",
                "question": "C++-ல் `std::move` மற்றும் Rvalue Reference (`&&`) மூலம் தேவையில்லாத டீப் காப்பிகளை (deep copy) எவ்வாறு தவிர்ப்பீர்கள்? `std::forward` எதற்காக தேவைப்படுகிறது?",
                "difficulty": "Medium",
                "concept": "Move Semantics"
            },
            {
                "id": 3,
                "title": "False Sharing மற்றும் கேச் அலைன்மெண்ட்",
                "question": "மல்டி-த்ரெடிங் இயக்கத்தில் False Sharing பிரச்சனையால் பல கோர்கள் இருக்கும்போது வேகம் குறைகிறது. `alignas` பயன்படுத்தி கேச் லைன் பேடிங் (cache line padding) செய்வதன் மூலம் இதனை எவ்வாறு தீர்ப்பீர்கள்?",
                "difficulty": "Medium",
                "concept": "Cache Coherence"
            },
            {
                "id": 4,
                "title": "Lock-Free கன்கரன்சி மற்றும் std::atomic",
                "question": "மியூடெக்ஸ் லாக் பயன்படுத்தாமல் `std::atomic` கொண்டு லாக்-ஃப்ரீ ரிங் பஃபரை (lock-free ring buffer) எவ்வாறு உருவாக்குவீர்கள்? `memory_order_acquire` மற்றும் `memory_order_release` எங்கு பயன்படுகின்றன?",
                "difficulty": "Medium-Hard",
                "concept": "Lock-Free Programming"
            },
            {
                "id": 5,
                "title": "C++20 கான்செப்ட்ஸ் (Concepts) மற்றும் டெம்ப்ளேட்கள்",
                "question": "பழைய C++ SFINAE மற்றும் `std::enable_if` சிக்கல்களுக்கு பதிலாக C++20 `concepts` மற்றும் `requires` கிளாஸ்களை எவ்வாறு பயன்படுத்துவீர்கள்?",
                "difficulty": "Hard",
                "concept": "C++20 Concepts"
            }
        ]
    },
    "C#": {
        "English": [
            {
                "id": 1,
                "title": "Async/Await State Machine and Thread Pool Starvation",
                "question": "In an ASP.NET Core web API, synchronous calls to `.Result` or `.Wait()` on asynchronous Tasks intermittently freeze request processing. Explain how the compiler-generated async state machine works, why sync-over-async causes thread pool starvation, and how to fix it.",
                "difficulty": "Easy-Medium",
                "concept": "Task Parallel Library & Async State Machine"
            },
            {
                "id": 2,
                "title": "Zero-Allocation Parsing with Span<T> and Memory<T>",
                "question": "A high-volume telemetry ingestion service generates excessive Generation 0 and Large Object Heap (LOH) garbage collections when substringing strings and copying byte buffers. How would you refactor the parsing engine using `ReadOnlySpan<T>` and `Memory<T>` for zero-allocation performance?",
                "difficulty": "Medium",
                "concept": "Span<T>, Memory<T> & LOH Management"
            },
            {
                "id": 3,
                "title": "Handling DbContext Concurrency in Entity Framework Core",
                "question": "A background task in .NET injects a single scoped `DbContext` instance across multiple concurrent worker threads, throwing `InvalidOperationException: A second operation was started on this context instance before a previous operation completed`. How do you properly handle Entity Framework Core concurrency using `IDbContextFactory`?",
                "difficulty": "Medium",
                "concept": "EF Core Concurrency & Scoped Lifetimes"
            },
            {
                "id": 4,
                "title": "High-Throughput Producer-Consumer with System.Threading.Channels",
                "question": "When designing an in-memory queueing mechanism between fast incoming webhook publishers and slow database batch writers, why are `System.Threading.Channels` preferred over `BlockingCollection<T>` or `ConcurrentQueue<T>`? Detail backpressure handling with bounded channels.",
                "difficulty": "Medium-Hard",
                "concept": "Channels & Backpressure"
            },
            {
                "id": 5,
                "title": "Garbage Collector Internals and Finalization Pipeline",
                "question": "Explain the architectural differences between Workstation and Server GC in .NET. How does the `IDisposable` pattern combined with `GC.SuppressFinalize(this)` prevent costly Gen 2 finalization queue bottlenecks when releasing unmanaged handles?",
                "difficulty": "Hard",
                "concept": "GC Generations & IDisposable"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "C# Async/Await மற்றும் Thread Pool Starvation",
                "question": "ASP.NET Core அப்ளிகேஷனில் `.Result` அல்லது `.Wait()` அழைக்கும் போது சர்வர் முடங்குகிறது. compiler-generated async state machine எவ்வாறு இயங்குகிறது? Thread Pool Starvation பிரச்சனையை எவ்வாறு தீர்ப்பீர்கள்?",
                "difficulty": "Easy-Medium",
                "concept": "Task Parallel Library"
            },
            {
                "id": 2,
                "title": "Span<T> மற்றும் Memory<T> கொண்டு ஜீரோ-மெமரி பார்சிங்",
                "question": "அதிக தரவு வரும்போது ஸ்ட்ரிங் சப்ஸ்ட்ரிங் செய்வதால் Garbage Collection அதிகம் நடக்கிறது. `Span<T>` மற்றும் `Memory<T>` பயன்படுத்தி நினைவக ஒதுக்கீடே இல்லாமல் (zero-allocation) எவ்வாறு தகவலை பார்ஸ் செய்வீர்கள்?",
                "difficulty": "Medium",
                "concept": "Span<T> & Memory Optimization"
            },
            {
                "id": 3,
                "title": "Entity Framework Core மற்றும் DbContext கன்கரன்சி",
                "question": "ஒரே DbContext-ஐ பல திரெட்களில் இயக்கும் போது InvalidOperationException ஏற்படுகிறது. `IDbContextFactory` பயன்படுத்தி EF Core கன்கரன்சியை எவ்வாறு சரியாக அமைப்பீர்கள்?",
                "difficulty": "Medium",
                "concept": "EF Core Concurrency"
            },
            {
                "id": 4,
                "title": "System.Threading.Channels கொண்டு Producer-Consumer",
                "question": "வேகமாக வரும் வெப்ஹூக் தகவல்களை மெதுவாக டேட்டாபேஸில் எழுத `System.Threading.Channels` எவ்வாறு பயன்படுகிறது? பேக்பிரஷர் (backpressure) நிலையை எவ்வாறு கட்டுப்படுத்துவீர்கள்?",
                "difficulty": "Medium-Hard",
                "concept": "Channels & Backpressure"
            },
            {
                "id": 5,
                "title": ".NET கார்பேஜ் கலெக்டர் மற்றும் IDisposable பேட்டர்ன்",
                "question": ".NET-ல் Gen 0, Gen 1, Gen 2 மெமரி எவ்வாறு செயல்படுகிறது? `IDisposable` பேட்டர்னில் `GC.SuppressFinalize` பயன்பாடு என்ன?",
                "difficulty": "Hard",
                "concept": "GC Generations & IDisposable"
            }
        ]
    },
    "C": {
        "English": [
            {
                "id": 1,
                "title": "Manual Memory Allocation, Dangling Pointers and Double Free",
                "question": "A production C network daemon intermittently crashes with `Segmentation fault (core dumped)`. Inspection suggests an edge case where a client buffer is freed twice, or accessed after freeing. How do you guard against dangling pointers, use Valgrind to identify memory bugs, and safely structure dynamic memory lifecycles?",
                "difficulty": "Easy-Medium",
                "concept": "Memory Management & Valgrind"
            },
            {
                "id": 2,
                "title": "Struct Padding, Memory Alignment and Network Serialization",
                "question": "Sending a C struct directly across a socket between an x86 server and an ARM embedded device causes garbled data. Explain how struct padding and memory alignment work, why endianness differences cause serialization failures, and how to pack or serialize structs portably.",
                "difficulty": "Medium",
                "concept": "Data Alignment & Endianness"
            },
            {
                "id": 3,
                "title": "Safe String Handling and Buffer Overflow Prevention",
                "question": "Legacy C functions like `strcpy` and `sprintf` are notorious for stack-based buffer overflows. Why is `strncpy` still dangerous regarding null-termination, and how do modern safe alternatives like `snprintf` guarantee memory boundary integrity?",
                "difficulty": "Medium",
                "concept": "Buffer Overflows & Safe String Operations"
            },
            {
                "id": 4,
                "title": "POSIX Threads, Mutexes, and Condition Variables",
                "question": "In a multi-threaded C server using `pthread`, multiple worker threads wait for tasks from a shared linked-list queue. How do you properly implement producer-consumer synchronization using a `pthread_mutex_t` and `pthread_cond_t` while guarding against spurious wakeups?",
                "difficulty": "Medium-Hard",
                "concept": "Pthreads & Condition Variables"
            },
            {
                "id": 5,
                "title": "Non-Blocking I/O and Scalable Multiplexing with epoll",
                "question": "A single-threaded C chat server using `select()` degrades severely beyond 1,024 concurrent client sockets. How does Linux `epoll` provide $O(1)$ event notifications, and how do you handle partial writes and `EAGAIN`/`EWOULDBLOCK` in edge-triggered mode?",
                "difficulty": "Hard",
                "concept": "I/O Multiplexing & Edge-Triggered epoll"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "C மெமரி மேலாண்மை மற்றும் Double Free தடுப்பு",
                "question": "C மொழியில் எழுதப்பட்ட சர்வரில் Segmentation fault பிழை ஏற்படுகிறது. ஒரு பாயிண்டரை இருமுறை ஃப்ரீ (double free) செய்வதையும், Dangling pointer பிழைகளையும் Valgrind கொண்டு எவ்வாறு கண்டறிந்து சரிசெய்வீர்கள்?",
                "difficulty": "Easy-Medium",
                "concept": "Dynamic Memory & Valgrind"
            },
            {
                "id": 2,
                "title": "Struct Padding மற்றும் நெட்வொர்க் சீரியலைசேஷன்",
                "question": "C struct-ஐ சாக்கெட் வழியாக x86-லிருந்து ARM சாதனத்திற்கு அனுப்பும்போது தவறான தகவல்கள் வருகின்றன. Struct padding மற்றும் Endianness வேறுபாடுகளை எவ்வாறு கையாளுவீர்கள்?",
                "difficulty": "Medium",
                "concept": "Struct Alignment & Endianness"
            },
            {
                "id": 3,
                "title": "Buffer Overflow மற்றும் பாதுகாப்பான ஸ்ட்ரிங் கையாளுதல்",
                "question": "பழைய `strcpy` செயற்கூறு Buffer Overflow பாதுகாப்பு அச்சுறுத்தலை ஏற்படுத்துகிறது. `snprintf` எவ்வாறு நினைவக எல்லையை பாதுகாக்கிறது?",
                "difficulty": "Medium",
                "concept": "Buffer Overflows & snprintf"
            },
            {
                "id": 4,
                "title": "Pthreads, மியூடெக்ஸ் மற்றும் Condition Variables",
                "question": "`pthread` பயன்படுத்தி ஒரு producer-consumer கியூவை (queue) எவ்வாறு உருவாக்குவீர்கள்? spurious wakeups-லிருந்து condition variable-ஐ பாதுகாக்க என்ன செய்ய வேண்டும்?",
                "difficulty": "Medium-Hard",
                "concept": "Pthreads & Condition Variables"
            },
            {
                "id": 5,
                "title": "Linux epoll கொண்டு அதிக இணைப்புகளை கையாளுதல்",
                "question": "1,000-க்கும் மேற்பட்ட சாக்கெட் இணைப்புகள் வரும்போது `select()` மெதுவாகிறது. லினக்ஸ் `epoll` கொண்டு non-blocking I/O மற்றும் edge-triggered முறையில் இதனை எவ்வாறு வேகப்படுத்துவீர்கள்?",
                "difficulty": "Hard",
                "concept": "epoll & Non-blocking I/O"
            }
        ]
    },
    "SQL": {
        "English": [
            {
                "id": 1,
                "title": "Query Optimization using EXPLAIN ANALYZE and Indexing",
                "question": "A relational database query taking 45 seconds to scan a 10-million row orders table causes web timeouts. How do you interpret an `EXPLAIN ANALYZE` query execution plan, identify Sequential Scans versus Index Scans, and design a composite B-Tree index to satisfy filtering and sorting?",
                "difficulty": "Easy-Medium",
                "concept": "EXPLAIN ANALYZE & Composite Indexes"
            },
            {
                "id": 2,
                "title": "ACID Isolation Levels, Dirty Reads and Phantom Reads",
                "question": "Contrast Read Committed, Repeatable Read, and Serializable transaction isolation levels. In a banking application, what anomalous phenomena (such as Non-Repeatable Reads or Write Skew) can occur under lower isolation levels, and how does MVCC mitigate locking overhead?",
                "difficulty": "Medium",
                "concept": "Transaction Isolation Levels & MVCC"
            },
            {
                "id": 3,
                "title": "Preventing and Resolving Relational Database Deadlocks",
                "question": "Two concurrent stored procedures updating accounts and audit logs in reverse order frequently fail with PostgreSQL/MySQL Deadlock errors (`Deadlock found when trying to get lock`). How do you systematically restructure table update orders and configure lock timeouts to eradicate deadlocks?",
                "difficulty": "Medium",
                "concept": "Deadlock Detection & Resolution"
            },
            {
                "id": 4,
                "title": "Window Functions vs Group By for Complex Analytical Aggregations",
                "question": "Write and explain a SQL query utilizing window functions (`ROW_NUMBER()`, `RANK()`, and `PARTITION BY`) to determine the top 3 highest-spending customers for each country within a given fiscal quarter without writing expensive nested subqueries.",
                "difficulty": "Medium-Hard",
                "concept": "Window Functions & Partitioning"
            },
            {
                "id": 5,
                "title": "Table Partitioning, Sharding, and Index Maintenance on Billions of Rows",
                "question": "A historical audit table exceeds 2 billion rows, degrading write throughput and backup operations. How would you implement declarative range partitioning by date, manage partition pruning, and optimize index bloat on high-write systems?",
                "difficulty": "Hard",
                "concept": "Table Partitioning & Sharding"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "EXPLAIN ANALYZE மற்றும் இன்டெக்ஸ் உகப்பாக்கம்",
                "question": "1 கோடி வரிசைகள் கொண்ட அட்டவணையில் குவெரி 45 விநாடிகள் எடுப்பதால் டைம்அவுட் ஆகிறது. `EXPLAIN ANALYZE` கொண்டு sequential scan-ஐ index scan-ஆக மாற்ற சரியான Composite B-Tree இன்டெக்ஸை எவ்வாறு உருவாக்குவீர்கள்?",
                "difficulty": "Easy-Medium",
                "concept": "EXPLAIN ANALYZE & B-Tree Indexes"
            },
            {
                "id": 2,
                "title": "ACID பரிவர்த்தனை நிலை மற்றும் Dirty Reads",
                "question": "Read Committed, Repeatable Read, மற்றும் Serializable இடையே உள்ள வேறுபாடுகள் என்ன? வங்கி அமைப்புகளில் Dirty Reads மற்றும் Phantom Reads பிரச்சனைகளை MVCC எவ்வாறு தடுக்கிறது?",
                "difficulty": "Medium",
                "concept": "ACID & MVCC"
            },
            {
                "id": 3,
                "title": "டேட்டாபேஸ் டெட்லாக் தவிர்த்தல்",
                "question": "ஒரே நேரத்தில் இரண்டு குவெரிகள் அட்டவணைகளை மாற்றி மாற்றி லாக் செய்வதால் Deadlock ஏற்படுகிறது. அட்டவணை புதுப்பிக்கும் வரிசையை (update order) மாற்றி இந்த டெட்லாக்கை எவ்வாறு தீர்ப்பீர்கள்?",
                "difficulty": "Medium",
                "concept": "Deadlock Prevention"
            },
            {
                "id": 4,
                "title": "Window Functions கொண்டு பகுப்பாய்வு",
                "question": "`ROW_NUMBER()`, `RANK()`, மற்றும் `PARTITION BY` போன்ற Window Functions பயன்படுத்தி ஒவ்வொரு நாட்டிலும் அதிக பணம் செலவழித்த முதல் 3 வாடிக்கையாளர்களை எவ்வாறு கண்டறிவீர்கள்?",
                "difficulty": "Medium-Hard",
                "concept": "Window Functions"
            },
            {
                "id": 5,
                "title": "கோடிக்கணக்கான பதிவுகளுக்கு Table Partitioning",
                "question": "200 கோடி பதிவுகள் கொண்ட அட்டவணையில் தேடல்கள் மிக மெதுவாகின்றன. தேதி வாரியாக Range Partitioning செய்து Partition Pruning மூலம் வேகத்தை எவ்வாறு அதிகரிப்பீர்கள்?",
                "difficulty": "Hard",
                "concept": "Table Partitioning"
            }
        ]
    },
    "Go": {
        "English": [
            {
                "id": 1,
                "title": "Goroutine Leaks and Context Cancellation",
                "question": "A Go web microservice shows memory consumption climbing steadily after running for several days. Profiling with `pprof` indicates tens of thousands of idle goroutines waiting on unbuffered channels whose receivers have terminated. How do you use `context.Context` with `context.WithTimeout` and `context.WithCancel` to prevent goroutine leaks?",
                "difficulty": "Easy-Medium",
                "concept": "Goroutine Leaks & Context Lifecycle"
            },
            {
                "id": 2,
                "title": "Buffered vs Unbuffered Channels and Worker Pools",
                "question": "Design an in-memory worker pool in Go that consumes tasks from an incoming channel with a fixed concurrency of 20 workers, publishes results to an output channel, and gracefully shuts down without losing in-flight jobs using `sync.WaitGroup`.",
                "difficulty": "Medium",
                "concept": "Channels & Worker Pool Pattern"
            },
            {
                "id": 3,
                "title": "Race Conditions, Data Races and sync.Mutex vs sync.RWMutex",
                "question": "Running `go test -race` detects a data race on an in-memory session cache accessed concurrently by HTTP request handlers. When would you choose `sync.RWMutex` over standard `sync.Mutex`, and what are the performance trade-offs under high-write workloads?",
                "difficulty": "Medium",
                "concept": "Race Detector & RWMutex"
            },
            {
                "id": 4,
                "title": "Slices Internals, Memory Reallocation and Hidden Subslice Leaks",
                "question": "Extracting a 10-byte substring from a 50-megabyte file using `sub := largeBuffer[:10]` keeps the entire 50-megabyte array pinned in memory by the Go garbage collector. Explain slice header internals (pointer, len, cap) and how `copy()` avoids holding the underlying backing array.",
                "difficulty": "Medium-Hard",
                "concept": "Slice Internals & Memory Retention"
            },
            {
                "id": 5,
                "title": "Go Garbage Collector Tuning and Escape Analysis",
                "question": "In a low-latency financial trading microservice written in Go, frequent GC cycles cause microsecond latency spikes. How do you analyze compiler escape analysis (`-gcflags='-m'`) to prevent heap allocations, utilize `sync.Pool`, and tune the `GOGC` / `GOMEMLIMIT` environment parameters?",
                "difficulty": "Hard",
                "concept": "Escape Analysis, sync.Pool & GOGC"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "Go மொழியில் Goroutine கசிவு மற்றும் Context",
                "question": "கோ மொழியில் இயங்கும் சர்வரில் Goroutine leak ஏற்பட்டு மெமரி நிரம்புகிறது. `context.Context`, `context.WithTimeout` மற்றும் சேனல்களை கொண்டு இந்த முடங்கிய கோரூட்டின்களை எவ்வாறு பாதுகாப்பாக நிறுத்துவீர்கள்?",
                "difficulty": "Easy-Medium",
                "concept": "Goroutines & Context"
            },
            {
                "id": 2,
                "title": "சேனல்கள் மற்றும் Worker Pool பேட்டர்ன்",
                "question": "20 worker goroutine-கள் கொண்ட ஒரு ஒர்க்கர் பூலை (worker pool) கோ மொழியில் எவ்வாறு வடிவமைப்பீர்கள்? `sync.WaitGroup` கொண்டு அனைத்து வேலைகளும் முடிந்ததும் எவ்வாறு சர்வீஸை பாதுகாப்பாக மூடுவீர்கள்?",
                "difficulty": "Medium",
                "concept": "Channels & Worker Pools"
            },
            {
                "id": 3,
                "title": "Data Race தவிர்த்தல் மற்றும் RWMutex",
                "question": "`go test -race` இயக்கும் போது டேட்டா ரேஸ் பிழை காட்டுகிறது. `sync.Mutex` மற்றும் `sync.RWMutex` இடையே உள்ள வேறுபாடுகள் என்ன? அதிக வாசிப்பு (read-heavy) சூழலில் எதை தேர்ந்தெடுப்பீர்கள்?",
                "difficulty": "Medium",
                "concept": "Race Detector & RWMutex"
            },
            {
                "id": 4,
                "title": "Slice நினைவக ஒதுக்கீடு மற்றும் சப்-ஸ்லைஸ் கசிவு",
                "question": "பெரிய பைலில் இருந்து சிறிய பகுதியை `largeBuffer[:10]` என எடுக்கும் போது முழு பைலும் நினைவகத்தில் தங்கிவிடுகிறது. Slice header (pointer, len, cap) எவ்வாறு இயங்குகிறது? `copy()` கொண்டு இதனை எவ்வாறு சரிசெய்வீர்கள்?",
                "difficulty": "Medium-Hard",
                "concept": "Slice Internals & GC"
            },
            {
                "id": 5,
                "title": "Escape Analysis மற்றும் sync.Pool",
                "question": "கோ கார்பேஜ் கலெக்ஷன் தாமதங்களை குறைக்க Escape Analysis (`-gcflags='-m'`) மற்றும் `sync.Pool` எவ்வாறு உதவுகிறது? `GOGC` மற்றும் `GOMEMLIMIT` அமைப்புகளை எவ்வாறு டியூன் செய்வீர்கள்?",
                "difficulty": "Hard",
                "concept": "Escape Analysis & sync.Pool"
            }
        ]
    },
    "Rust": {
        "English": [
            {
                "id": 1,
                "title": "Borrow Checker, Ownership and Lifetimes in Rust",
                "question": "A developer trying to build a shared cache in Rust encounters compiler errors: `cannot borrow as mutable more than once at a time`. Explain Rust's ownership and borrowing invariants, how non-lexical lifetimes (NLL) work, and how you resolve shared mutable state using safe patterns.",
                "difficulty": "Easy-Medium",
                "concept": "Ownership, Borrow Checker & Lifetimes"
            },
            {
                "id": 2,
                "title": "Shared Mutability with Rc/Arc and RefCell/Mutex",
                "question": "Contrast single-threaded interior mutability (`Rc<RefCell<T>>`) with multi-threaded thread-safe mutability (`Arc<Mutex<T>>` or `Arc<RwLock<T>>`). How does `RefCell` enforce borrowing rules dynamically at runtime, and what happens if a borrow is violated?",
                "difficulty": "Medium",
                "concept": "Arc, Mutex & Interior Mutability"
            },
            {
                "id": 3,
                "title": "Async Rust, Futures, and Pinning with Pin<&mut T>",
                "question": "In an asynchronous Tokio service, implementing a self-referential future causes compiler errors regarding the `Unpin` trait. Why is `Pin` required in async Rust to prevent self-referential structs from moving in memory, and how do async state machines rely on it?",
                "difficulty": "Medium",
                "concept": "Async Rust, Pinning & Tokio"
            },
            {
                "id": 4,
                "title": "Zero-Cost Abstractions and Trait Objects (Dynamic Dispatch)",
                "question": "Explain the difference between compile-time monomorphization (static dispatch with `impl Trait` or generics) and runtime dynamic dispatch with `Box<dyn Trait>` (vtable). What are the performance and binary size trade-offs in high-throughput engines?",
                "difficulty": "Medium-Hard",
                "concept": "Monomorphization vs Dynamic Dispatch"
            },
            {
                "id": 5,
                "title": "Safe Abstractions over Unsafe Rust and FFI",
                "question": "You are writing a Rust wrapper around a high-performance C shared library that exposes raw pointers. How do you design an idiomatic, safe Rust API boundary that upholds Rust's memory safety guarantees, prevents undefined behavior, and uses `std::mem::forget` or `ManuallyDrop` where appropriate?",
                "difficulty": "Hard",
                "concept": "Unsafe Rust, FFI & Invariants"
            }
        ],
        "Tamil": [
            {
                "id": 1,
                "title": "ரஸ்ட் (Rust) Ownership மற்றும் Borrow Checker",
                "question": "ரஸ்ட் மொழியில் `cannot borrow as mutable more than once` பிழை ஏற்படுகிறது. ரஸ்ட்டின் ஓனர்ஷிப் (Ownership), பாரோயிங் (Borrowing), மற்றும் லைஃப்டைம்ஸ் (Lifetimes) விதிகள் எவ்வாறு நினைவக பாதுகாப்பை உறுதி செய்கின்றன?",
                "difficulty": "Easy-Medium",
                "concept": "Ownership & Borrowing"
            },
            {
                "id": 2,
                "title": "Arc மற்றும் Mutex மூலம் பல த்ரெட்களில் டேட்டாவை பகிர்தல்",
                "question": "பல த்ரெட்களுக்கு இடையே ஒரே தரவை மாற்றுவதற்கு `Arc<Mutex<T>>` எவ்வாறு பயன்படுகிறது? சிங்கிள் த்ரெட் `Rc<RefCell<T>>` மற்றும் `Arc<Mutex<T>>` இடையே உள்ள வேறுபாடுகள் என்ன?",
                "difficulty": "Medium",
                "concept": "Arc & Mutex"
            },
            {
                "id": 3,
                "title": "Async Rust, Tokio மற்றும் Pinning",
                "question": "Tokio போன்ற Async சூழலில் Self-referential அமைப்புகள் நினைவகத்தில் நகர்வதை தடுக்க `Pin<&mut T>` எதற்காக தேவைப்படுகிறது?",
                "difficulty": "Medium",
                "concept": "Async Rust & Pinning"
            },
            {
                "id": 4,
                "title": "Static Dispatch (Generics) மற்றும் Dynamic Dispatch (`dyn Trait`)",
                "question": "கம்பைல்-டைம் Monomorphization (`impl Trait`) மற்றும் ரன்-டைம் Dynamic Dispatch (`Box<dyn Trait>`) இடையே உள்ள வேகம் மற்றும் நினைவக பயன்பாட்டு வேறுபாடுகள் என்ன?",
                "difficulty": "Medium-Hard",
                "concept": "Traits & Dispatch"
            },
            {
                "id": 5,
                "title": "Unsafe Rust மற்றும் C லைப்ரரி இணைப்பு (FFI)",
                "question": "C மொழியில் எழுதப்பட்ட லைப்ரரியை ரஸ்ட்டுடன் FFI வழியாக இணைக்கும் போது, பாதுகாப்பான ரஸ்ட் இடைமுகத்தை (safe wrapper) எவ்வாறு உருவாக்குவீர்கள்?",
                "difficulty": "Hard",
                "concept": "Unsafe Rust & FFI"
            }
        ]
    }
}


class QuestionGenerationService:
    def __init__(self):
        self._quota_exhausted_until: float = 0.0

    @property
    def api_key(self) -> str:
        # Re-read from env dynamically to always reflect .env updates without restarting
        load_dotenv(dotenv_path=ENV_PATH, override=True)
        return os.getenv("OPENAI_API_KEY", "").strip()

    def check_gpt_availability(self) -> Dict[str, Any]:
        """
        Verifies whether OpenAI API models are accessible with the configured key.
        """
        if not self.api_key:
            return {
                "available": False,
                "status": "missing_api_key",
                "message": "OPENAI_API_KEY is not configured in backend/.env"
            }

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, timeout=3.0, max_retries=0)
            models = client.models.list()
            model_ids = [m.id for m in models.data]

            usable_models = [m for m in ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo-0125"] if m in model_ids]

            return {
                "available": bool(usable_models),
                "status": "available" if usable_models else "quota_or_permission",
                "models": usable_models or model_ids[:5],
                "message": f"OpenAI API key loaded. Available target models: {usable_models}"
            }
        except Exception as e:
            return {
                "available": False,
                "status": "error",
                "message": f"OpenAI API check notice: {str(e)}"
            }

    # Backward compatibility alias
    def check_gpt35_turbo_availability(self) -> Dict[str, Any]:
        return self.check_gpt_availability()

    async def generate_questions(self, programming_language: str, assessment_language: str) -> List[Dict[str, Any]]:
        """
        Generates exactly five scenario-based questions in the chosen language.
        Tries OpenAI first with modern models (gpt-4o-mini, gpt-4o).
        If OpenAI is unconfigured or rate-limited/out-of-credits, seamlessly uses
        the rich, dedicated 5-question technical scenario bank for that specific language.
        """
        # Normalize inputs
        prog_lang = (programming_language or "Python").strip()
        assess_lang = (assessment_language or "English").strip()

        # Step 1: Attempt live OpenAI generation if API key is present and not in quota cooldown
        import time
        if self.api_key and time.time() > self._quota_exhausted_until:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key, timeout=5.0, max_retries=0)

                prompt = f"""You are an expert principal engineer creating oral technical interview questions for Vani AI.
Generate exactly 5 progressive, realistic scenario-based interview questions for a software engineer specializing in {prog_lang}.
Write every title and question entirely in {assess_lang}.

Each question must describe a concrete workplace situation with relevant context, a problem or goal, and practical constraints. Ask the candidate to explain how they would investigate, reason about, or make a decision in that situation. The questions must assess technical understanding through spoken explanations, not coding exercises.

Strictly do not include source code, pseudocode, code snippets, code blocks, commands, sample implementations, or code-like examples. Never ask the candidate to write, complete, fix, or output code. Ask for a verbal explanation of the approach, reasoning, and trade-offs instead.

Progress the difficulty as follows:
1. Practical scenario (Easy-Medium)
2. Concurrency or design scenario (Medium)
3. Tricky edge case or production incident (Medium)
4. Architectural trade-off or scaling scenario (Medium-Hard)
5. Deep technical reasoning or mission-critical recovery scenario (Hard)

Return a JSON object with a "questions" array containing exactly 5 objects. Each object must have:
- "id": integer from 1 to 5
- "title": a concise scenario title in {assess_lang}
- "question": a detailed, open-ended scenario question in {assess_lang}
- "difficulty": one of "Easy-Medium", "Medium", "Medium-Hard", or "Hard"
- "concept": the technical concept being evaluated

Return JSON only. Do not include markdown or any text outside the JSON object."""

                # Try modern active models in order
                candidate_models = ["gpt-4o-mini", "gpt-4o"]
                for model_name in candidate_models:
                    try:
                        logger.info(f"Requesting 5 {prog_lang} ({assess_lang}) questions via OpenAI {model_name}...")
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {
                                    "role": "system",
                                    "content": (
                                        "Return valid JSON only. Create oral, scenario-based interview "
                                        "questions and never include or request code."
                                    ),
                                },
                                {"role": "user", "content": prompt}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.75,
                            max_tokens=2000
                        )

                        content = response.choices[0].message.content.strip()
                        payload = json.loads(content)
                        questions = payload.get("questions") if isinstance(payload, dict) else None
                        required_fields = {"id", "title", "question", "difficulty", "concept"}
                        if (
                            isinstance(questions, list)
                            and len(questions) == 5
                            and all(
                                isinstance(question, dict)
                                and required_fields.issubset(question)
                                and question["id"] == expected_id
                                and all(
                                    isinstance(question[field], str) and question[field].strip()
                                    for field in ("title", "question", "difficulty", "concept")
                                )
                                and not any(
                                    marker in (question["title"] + question["question"]).lower()
                                    for marker in ("```", "`", "<code", "</code>")
                                )
                                for expected_id, question in enumerate(questions, start=1)
                            )
                        ):
                            logger.info(f"OpenAI {model_name} successfully generated 5 custom {prog_lang} ({assess_lang}) questions!")
                            return questions
                        raise ValueError(
                            "OpenAI returned questions with an invalid shape or code-formatted content."
                        )
                    except Exception as model_err:
                        err_str = str(model_err)
                        logger.warning(f"OpenAI model {model_name} attempt: {err_str}")
                        # If quota exhausted, unauthorized, or network connection failed, don't retry other models
                        lowered = err_str.lower()
                        if (
                            "insufficient_quota" in lowered
                            or "credit_balance_exhausted" in lowered
                            or "quota" in lowered
                            or "connection" in lowered
                            or "connect" in lowered
                            or "rate_limit" in lowered
                            or "unauthorized" in lowered
                            or "invalid_api_key" in lowered
                        ):
                            logger.info(f"OpenAI service notice ({model_err}). Initiating 60s cooldown; using dedicated scenario bank.")
                            self._quota_exhausted_until = time.time() + 60.0
                            break
                        continue

            except Exception as e:
                logger.warning(f"OpenAI question generation notice: {e}. Utilizing dedicated {prog_lang} scenario bank.")

        # Step 2: Dedicated Language Scenario Bank Fallback
        # Guarantee every selected language (Java, Python, C++, Go, Rust, SQL, JavaScript, TypeScript, C, C#)
        # receives distinct, highly authentic technical questions in either English or Tamil.
        matched_lang = None
        for key in QUESTION_BANKS.keys():
            if key.lower() == prog_lang.lower():
                matched_lang = key
                break

        if not matched_lang:
            # Handle partial matching (e.g. "c++" vs "cpp")
            if "c++" in prog_lang.lower(): matched_lang = "C++"
            elif "c#" in prog_lang.lower(): matched_lang = "C#"
            elif "type" in prog_lang.lower(): matched_lang = "TypeScript"
            elif "java" in prog_lang.lower() and "script" not in prog_lang.lower(): matched_lang = "Java"
            elif "sql" in prog_lang.lower(): matched_lang = "SQL"
            elif "rust" in prog_lang.lower(): matched_lang = "Rust"
            elif "go" in prog_lang.lower(): matched_lang = "Go"
            else: matched_lang = "Python"

        lang_bank = QUESTION_BANKS.get(matched_lang, QUESTION_BANKS["Python"])
        questions = lang_bank.get(assess_lang) or lang_bank.get("English") or QUESTION_BANKS["Python"]["English"]

        logger.info(f"Delivered 5 dedicated scenario questions for {matched_lang} in {assess_lang}.")
        return questions


question_service = QuestionGenerationService()
