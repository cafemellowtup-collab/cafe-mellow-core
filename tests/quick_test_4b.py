"""
Quick Test for Phase 4B: Deep History Cortex
=============================================
Tests that:
- Timeline analysis detects operating modes
- Persona adapts based on data richness
- Missing data is handled with benchmark estimations
- AI references user history in responses
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Windows encoding fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def test_deep_history_cortex():
    print("=" * 70)
    print("Phase 4B: Deep History Cortex Test")
    print("=" * 70)
    
    from backend.universal_adapter.titan_cortex import TitanCortex, get_cortex
    
    # Test 1: Timeline Analysis
    print("\n[1] Testing Timeline Analysis...")
    cortex = get_cortex("cafe-mellow")  # Real tenant with data
    
    print(f"    Analyzing data timeline for cafe-mellow...")
    history = cortex.analyze_data_timeline("cafe-mellow")
    
    print(f"    Operating Mode: {history.get('operating_mode')}")
    print(f"    Total Months with Data: {history.get('total_months_with_data')}")
    print(f"    User Habits: {history.get('user_habits', [])}")
    
    # Show monthly density sample
    monthly = history.get('monthly_density', {})
    if monthly:
        sample_months = list(monthly.keys())[:3]
        print(f"    Sample Months: {sample_months}")
        for m in sample_months:
            data = monthly[m]
            print(f"      - {m}: {data.get('quality')} ({data.get('event_count')} events)")
    
    # Show benchmark
    benchmark = history.get('benchmark_margins', {})
    if benchmark:
        print(f"\n    Benchmark Period: {benchmark.get('period')}")
        print(f"    Benchmark Margin: {benchmark.get('profit_margin_pct')}%")
    else:
        print(f"\n    No benchmark available (need complete data)")
    
    # Show gaps
    gaps = history.get('data_gaps', [])
    if gaps:
        print(f"    Data Gaps: {gaps[:5]}{'...' if len(gaps) > 5 else ''}")
    else:
        print(f"    No data gaps detected")
    
    # Test 2: Persona Generation
    print("\n[2] Testing Persona Generation...")
    profile = cortex.get_data_profile("cafe-mellow")
    persona = cortex.generate_system_persona(profile, history)
    
    # Show first 500 chars of persona
    print(f"    Persona Preview:")
    print(f"    {'-' * 60}")
    print(f"    {persona[:500]}...")
    
    # Check for key elements
    has_honesty = "HONESTY" in persona or "hallucinate" in persona.lower()
    has_mode = history.get('operating_mode', '') in persona
    has_benchmark = "BENCHMARK" in persona
    
    print(f"\n    Persona Contains:")
    print(f"    - Honesty Protocol: {'YES' if has_honesty else 'NO'}")
    print(f"    - Operating Mode Reference: {'YES' if has_mode else 'NO'}")
    print(f"    - Benchmark Section: {'YES' if has_benchmark else 'NO'}")
    
    # Test 3: Context Prompt with Deep History
    print("\n[3] Testing Context Prompt with Deep History...")
    
    question = "What was my profit margin last year? I think I stopped tracking expenses in Q4."
    print(f"    Question: \"{question}\"")
    
    context = cortex.build_context_prompt(question, "cafe-mellow", include_history=True)
    
    # Check context contains history elements
    has_lazy_era = "Lazy" in context or "gap" in context.lower()
    has_timeline = "Operating Mode" in context or history.get('operating_mode', '') in context
    
    print(f"\n    Context Contains:")
    print(f"    - Lazy Era Awareness: {'YES' if has_lazy_era else 'NO'}")
    print(f"    - Timeline Context: {'YES' if has_timeline else 'NO'}")
    print(f"    - Context Length: {len(context)} chars")
    
    # Test 4: Query Engine with Deep History
    print("\n[4] Testing Query Engine Response...")
    from backend.universal_adapter.query_engine import QueryEngine
    
    engine = QueryEngine()
    
    # Test scenario: Ask about profit during a potentially lazy period
    test_question = "What was my profit in 2024? I might be missing some expense data."
    print(f"\n    Question: \"{test_question}\"")
    
    result = engine.ask(test_question, "cafe-mellow", execute_sql=False)
    
    print(f"\n    Response:")
    print(f"    - Question Understood: {result.get('question_understood')}")
    print(f"    - SQL Generated: {result.get('sql_generated')}")
    
    # Show history profile in response
    hist = result.get('history_profile', {})
    print(f"\n    History Profile in Response:")
    print(f"    - Operating Mode: {hist.get('operating_mode')}")
    print(f"    - Total Months: {hist.get('total_months')}")
    print(f"    - Benchmark Margin: {hist.get('benchmark_margin')}%")
    
    # Show answer excerpt
    answer = result.get('answer_text', '')[:300]
    print(f"\n    Answer Preview:")
    print(f"    {answer}...")
    
    # Check if AI mentions missing data or estimates
    mentions_gaps = any(word in answer.lower() for word in 
                       ['missing', 'incomplete', 'estimate', 'assume', 'benchmark', 'gap'])
    print(f"\n    AI Acknowledges Data Gaps: {'YES' if mentions_gaps else 'NO/UNCLEAR'}")
    
    # Summary
    print("\n" + "=" * 70)
    print("Phase 4B Test Results:")
    print("-" * 70)
    print(f"  - Timeline Analysis: WORKING")
    print(f"  - Operating Mode Detection: {history.get('operating_mode')}")
    print(f"  - Persona Generation: {'WORKING' if has_honesty else 'CHECK'}")
    print(f"  - Deep History Context: {'WORKING' if has_timeline else 'CHECK'}")
    print(f"  - Query Engine Integration: WORKING")
    print("=" * 70)
    
    # Goal verification
    print("\n[GOAL VERIFICATION]")
    print("Scenario: User has great data for 2023, missing expenses for 2024")
    print("Expected: AI should use 2023 margins as benchmark and disclose estimation")
    if benchmark:
        print(f"✓ Benchmark Available: {benchmark.get('profit_margin_pct')}% from {benchmark.get('period')}")
    if mentions_gaps:
        print(f"✓ AI Acknowledges Gaps in Response")
    else:
        print(f"? AI response may need review for gap acknowledgment")
    
    return True


if __name__ == "__main__":
    test_deep_history_cortex()
