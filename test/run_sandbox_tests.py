#!/usr/bin/env python3
"""Fleet Tactical Sandbox - Dedicated Test Runner
Runs only sandbox-related tests matching SPEC v1.0.
"""

import sys
import unittest
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_sandbox_tests():
    print("=" * 80)
    print(" FLEET TACTICAL SANDBOX v1.0 - 자동 불변식 및 단위 테스트")
    print(f" 테스트 경로: {PROJECT_ROOT / 'test'}")
    print(" 대상: test_sandbox_*.py")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(PROJECT_ROOT / "test"),
        pattern="test_sandbox_*.py",
    )

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    duration = time.time() - start_time

    print("\n" + "=" * 80)
    print(" [FLEET TACTICAL SANDBOX 불변식 검증 요약]")
    print(f" - 총 실행 테스트: {result.testsRun}")
    print(f" - 통과 (Success): {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f" - 실패 (Failures): {len(result.failures)}")
    print(f" - 오류 (Errors): {len(result.errors)}")
    print(f" - 소요 시간: {duration:.4f}초")
    print("=" * 80)

    if result.wasSuccessful():
        print(">> [PASS] 샌드박스 12대 시뮬레이션 불변식 및 물리/전투/AI 테스트가 100% 통과되었습니다.")
        return 0
    else:
        print(">> [FAIL] 불변식 위반 또는 테스트 오류가 발생하였습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(run_sandbox_tests())
