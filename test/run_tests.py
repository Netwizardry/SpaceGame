#!/usr/bin/env python3
"""SpaceGame v0.1 Test Runner Program
Runs all unit and integration tests located under test/
Reports mechanical verification results matching docs/spec.
"""

import sys
import unittest
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def run_all_tests():
    print("=" * 80)
    print(" SpaceGame v0.1 우주함대전 기계 명세 검증 테스트 프로그램")
    print(f" 테스트 경로: {PROJECT_ROOT / 'test'}")
    print("=" * 80)

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=str(PROJECT_ROOT / "test"), pattern="test_*.py")

    start_time = time.time()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    duration = time.time() - start_time

    print("\n" + "=" * 80)
    print(" [명세서 대조 검증 요약 보고서]")
    print(f" - 총 실행 테스트 수: {result.testsRun}")
    print(f" - 성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f" - 실패 (Failures): {len(result.failures)}")
    print(f" - 오류 (Errors): {len(result.errors)}")
    print(f" - 소요 시간: {duration:.4f}초")
    print("=" * 80)

    if result.wasSuccessful():
        print(">> [PASS] 모든 우주함대전 기계 명세 테스트가 100% 통과되었습니다.")
        return 0
    else:
        print(">> [FAIL] 명세 불일치 또는 테스트 오류가 발생하였습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
