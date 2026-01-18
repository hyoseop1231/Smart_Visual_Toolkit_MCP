---
id: SPEC-GALLERY-001
related_spec: spec.md
version: "1.0.0"
status: "draft"
created: "2026-01-19"
updated: "2026-01-19"
author: "Hyoseop"
tags: ["gallery", "acceptance-criteria", "gherkin"]
---

# SPEC-GALLERY-001: 수락 기준

## 1. 개요

본 문서는 이미지 갤러리 및 히스토리 관리 기능의 수락 기준을 정의합니다. Gherkin 형식(Given-When-Then)으로 작성된 시나리오를 통해 구현 완료 여부를 검증합니다.

---

## 2. 정의 (Definition)

### 2.1 Given-When-Then 형식

- **Given**: 선행 조건 (시스템 상태)
- **When**: 트리거 동작 (사용자 행위)
- **Then**: 예상 결과 (시스템 반응)

### 2.2 테스트 데이터

**기본 테스트 이미지**:
```
image_20250115_abc123.png - 스타일: cinematic, 날짜: 2025-01-15
image_20250116_def456.png - 스타일: anime, 날짜: 2025-01-16
image_20250117_ghi789.png - 스타일: cinematic, 날짜: 2025-01-17
image_20250118_jkl012.png - 스타일: watercolor, 날짜: 2025-01-18
```

---

## 3. 기능 수락 기준

### 3.1 이미지 목록 조회 (Feature: list_images)

#### TC-001: 기본 목록 조회

**Given** 사용자가 4개의 이미지를 생성했을 때
**When** `list_images()` 도구를 호출하면
**Then** 4개의 이미지 메타데이터가 반환되어야 한다
**And** 각 이미지는 id, filename, created_at, prompt, style 필드를 포함해야 한다
**And** 결과는 최신순(created_at 내림차순)으로 정렬되어야 한다

#### TC-002: 페이지네이션

**Given** 사용자가 100개의 이미지를 생성했을 때
**When** `list_images(limit=10, offset=0)` 도구를 호출하면
**Then** 10개의 이미지만 반환되어야 한다
**And** `total_count`는 100이어야 한다
**When** `list_images(limit=10, offset=10)` 도구를 호출하면
**Then** 다음 10개의 이미지가 반환되어야 한다

#### TC-003: 정렬 옵션

**Given** 사용자가 여러 이미지를 생성했을 때
**When** `list_images(sort_by="size", sort_order="asc")` 도구를 호출하면
**Then** 이미지가 크기 오름차순으로 정렬되어야 한다
**When** `list_images(sort_by="style", sort_order="desc")` 도구를 호출하면
**Then** 이미지가 스타일 내림차순으로 정렬되어야 한다

### 3.2 이미지 검색 (Feature: search_images)

#### TC-004: 스타일 필터링

**Given** 사용자가 cinematic 스타일 2개, anime 1개, watercolor 1개를 생성했을 때
**When** `search_images(style="cinematic")` 도구를 호출하면
**Then** 2개의 cinematic 이미지만 반환되어야 한다
**And** `matched_count`는 2이어야 한다

#### TC-005: 날짜 범위 필터링

**Given** 사용자가 2025-01-15, 2025-01-16, 2025-01-17에 이미지를 생성했을 때
**When** `search_images(date_from="2025-01-16", date_to="2025-01-17")` 도구를 호출하면
**Then** 2025-01-16, 2025-01-17의 이미지만 반환되어야 한다
**And** 2025-01-15의 이미지는 포함되지 않아야 한다

#### TC-006: 키워드 검색

**Given** 사용자가 프롬프트에 "sunset"이 포함된 이미지와 "mountain"이 포함된 이미지를 생성했을 때
**When** `search_images(keyword="sunset")` 도구를 호출하면
**Then** 프롬프트에 "sunset"이 포함된 이미지만 반환되어야 한다

#### TC-007: 복합 조건 검색

**Given** 사용자가 다양한 스타일과 날짜의 이미지를 생성했을 때
**When** `search_images(style="cinematic", date_from="2025-01-16", keyword="beautiful")` 도구를 호출하면
**Then** 모든 조건을 만족하는 이미지만 반환되어야 한다
**And** 조건을 만족하지 않는 이미지는 제외되어야 한다

#### TC-008: 검색 결과 없음

**Given** 사용자가 이미지를 생성했을 때
**When** `search_images(style="nonexistent")` 도구를 호출하면
**Then** 빈 목록이 반환되어야 한다
**And** `matched_count`는 0이어야 한다
**And** 성공 메시지("검색 결과가 없습니다")가 포함되어야 한다

### 3.3 이미지 상세 조회 (Feature: get_image_details)

#### TC-009: 존재하는 이미지 상세 조회

**Given** 사용자가 ID가 "img_20250115_abc123"인 이미지를 생성했을 때
**When** `get_image_details(image_id="img_20250115_abc123")` 도구를 호출하면
**Then** 전체 메타데이터가 반환되어야 한다
**And** 모든 필드(id, filename, filepath, prompt, style, resolution, size_bytes 등)가 포함되어야 한다
**And** `exists`는 `true`여야 한다

#### TC-010: 존재하지 않는 이미지 조회

**Given** 사용자가 이미지를 생성했을 때
**When** `get_image_details(image_id="nonexistent")` 도구를 호출하면
**Then** `success`는 `false`여야 한다
**And** 에러 메시지("이미지를 찾을 수 없습니다")가 반환되어야 한다

### 3.4 이미지 삭제 (Feature: delete_image)

#### TC-011: confirm 없는 삭제 시도

**Given** 사용자가 ID가 "img_20250115_abc123"인 이미지를 생성했을 때
**When** `delete_image(image_id="img_20250115_abc123", confirm=False)` 도구를 호출하면
**Then** 이미지는 삭제되지 않아야 한다
**And** 경고 메시지("confirm=True가 필요합니다")가 반환되어야 한다

#### TC-012: confirm 있는 삭제

**Given** 사용자가 ID가 "img_20250115_abc123"인 이미지를 생성했을 때
**And** 파일 시스템에 해당 파일이 존재할 때
**When** `delete_image(image_id="img_20250115_abc123", confirm=True)` 도구를 호출하면
**Then** 이미지 파일이 삭제되어야 한다
**And** 메타데이터에서도 제거되어야 한다
**And** `deleted`는 `true`여야 한다
**And** 성공 메시지가 반환되어야 한다

#### TC-013: 존재하지 않는 이미지 삭제

**Given** 사용자가 이미지를 생성했을 때
**When** `delete_image(image_id="nonexistent", confirm=True)` 도구를 호출하면
**Then** `success`는 `false`여야 한다
**And** 에러 메시지("이미지를 찾을 수 없습니다")가 반환되어야 한다

#### TC-014: 파일만 존재하고 메타데이터 없는 경우

**Given** 파일 시스템에는 이미지 파일이 존재하지만
**And** 메타데이터에는 없는 상태일 때
**When** `delete_image(image_id="orphaned", confirm=True)` 도구를 호출하면
**Then** 파일 시스템에서만 삭제가 시도되어야 한다
**And** 적절한 메시지가 반환되어야 한다

### 3.5 오래된 이미지 정리 (Feature: cleanup_old_images)

#### TC-015: dry-run 모드

**Given** 사용자가 30일 전, 20일 전, 10일 전 이미지를 생성했을 때
**When** `cleanup_old_images(days=30, dry_run=True)` 도구를 호출하면
**Then** 실제로는 삭제되지 않아야 한다
**And** 30일 이상된 이미지 목록이 반환되어야 한다
**And** `deleted_count`는 0이어야 한다
**And** `would_delete_count`는 예상 개수여야 한다

#### TC-016: 실제 정리 실행

**Given** 사용자가 30일 전, 20일 전, 10일 전 이미지를 생성했을 때
**When** `cleanup_old_images(days=30, dry_run=False)` 도구를 호출하면
**Then** 30일 이상된 이미지만 삭제되어야 한다
**And** 최근 20일, 10일 전 이미지는 유지되어야 한다
**And** `deleted_count`는 삭제된 개수여야 한다
**And** `freed_space_bytes`는 해제된 공간이어야 한다

#### TC-017: 정리 대상 없음

**Given** 사용자가 모두 7일 전 이미지만 생성했을 때
**When** `cleanup_old_images(days=30)` 도구를 호출하면
**Then** 삭제된 이미지가 없어야 한다
**And** `deleted_count`는 0이어야 한다
**And** "정리할 이미지가 없습니다" 메시지가 반환되어야 한다

### 3.6 메타데이터 일관성 (Feature: metadata_consistency)

#### TC-018: 이미지 생성 시 자동 등록

**Given** 갤러리 시스템이 활성화되어 있을 때
**When** `generate_image()` 도구를 호출하여 이미지를 생성하면
**Then** 메타데이터가 자동으로 생성/저장되어야 한다
**And** 메타데이터 파일(metadata.json)이 갱신되어야 한다

#### TC-019: 고아 메타데이터 정리

**Given** 메타데이터에는 이미지가 있지만
**And** 파일 시스템에는 파일이 없는 상태일 때
**When** `list_images()` 도구를 호출하면
**Then** 파일이 없는 메타데이터는 자동으로 제거되어야 한다
**And** 경고 로그가 기록되어야 한다

#### TC-020: 메타데이터 파일 복구

**Given** 메타데이터 파일이 손상되었을 때
**And** 파일 시스템에는 이미지 파일들이 존재할 때
**When** 갤러리 시스템이 초기화되면
**Then** 이미지 파일에서 메타데이터를 복구 시도해야 한다
**And** 복구된 메타데이터 수가 로그되어야 한다

### 3.7 썸네일 기능 (Feature: thumbnails)

#### TC-021: 썸네일 활성화 시 생성

**Given** `GALLERY_THUMBNAILS_ENABLED=true`로 설정되어 있을 때
**When** 새로운 이미지가 생성되면
**Then** 썸네일이 자동으로 생성되어야 한다
**And** `thumbnail_path` 필드가 채워져야 한다
**And** 썸네일 크기는 256x256 픽셀이어야 한다

#### TC-022: 썸네일 비활성화

**Given** `GALLERY_THUMBNAILS_ENABLED=false`로 설정되어 있을 때
**When** 새로운 이미지가 생성되면
**Then** 썸네일이 생성되지 않아야 한다
**And** `thumbnail_path` 필드는 `null`이어야 한다

#### TC-023: 썸네일 생성 실패 시

**Given** `GALLERY_THUMBNAILS_ENABLED=true`로 설정되어 있을 때
**And** Pillow 라이브러리가 없을 때
**When** 새로운 이미지가 생성되면
**Then** 이미지 생성은 성공해야 한다
**And** 썸네일 생성 실패가 로그되어야 한다
**And** `thumbnail_path`는 `null`이어야 한다
**And** 사용자에게는 영향이 없어야 한다

#### TC-024: 썸네일 포함 목록 조회

**Given** 썸네일이 있는 이미지들이 있을 때
**When** `list_images()` 도구를 호출하면
**Then** 각 이미지 메타데이터에 `thumbnail_path`가 포함되어야 한다
**And** 썸네일 경로가 유효해야 한다

---

## 4. 비기능 수락 기준

### 4.1 성능 기준

#### TC-PERF-001: 목록 조회 성능

**Given** 1000개의 이미지가 저장되어 있을 때
**When** `list_images(limit=50)` 도구를 호출하면
**Then** 1초 이내에 응답해야 한다

#### TC-PERF-002: 검색 성능

**Given** 1000개의 이미지가 저장되어 있을 때
**When** `search_images(style="cinematic")` 도구를 호출하면
**Then** 2초 이내에 응답해야 한다

#### TC-PERF-003: 메타데이터 로드

**Given** 메타데이터 파일이 존재할 때
**When** 갤러리 시스템이 초기화되면
**Then** 메타데이터 로드는 0.5초 이내에 완료되어야 한다

### 4.2 보안 기준

#### TC-SEC-001: 경로 검증

**Given** 악의적인 사용자가 "../../etc/passwd"와 같은 경로로 조회를 시도할 때
**When** `get_image_details()` 도구를 호출하면
**Then** 요청이 거부되어야 한다
**And** 에러 메시지가 반환되어야 한다

#### TC-SEC-002: 삭제 확인

**Given** 사용자가 이미지를 삭제하려 할 때
**When** `confirm=False`로 `delete_image()` 도구를 호출하면
**Then** 삭제가 수행되지 않아야 한다

### 4.3 데이터 무결성 기준

#### TC-INT-001: 메타데이터 파일 존재

**Given** 갤러리 시스템이 초기화될 때
**When** 메타데이터 파일이 없으면
**Then** 빈 메타데이터로 초기화되어야 한다
**And** 파일이 생성되어야 한다

#### TC-INT-002: 동시성 안전성

**Given** 두 개의 이미지가 동시에 생성될 때
**When** 두 `generate_image()` 호출이 동시에 실행되면
**Then** 메타데이터 파일이 손상되지 않아야 한다
**And** 두 이미지 모두 등록되어야 한다

---

## 5. Definition of Done

### 5.1 코드 완료 기준

- [ ] 모든 MCP 도구가 구현되어 있음
- [ ] 단위 테스트가 85% 이상 커버
- [ ] 통합 테스트가 모든 시나리오 통과
- [ ] 코드가 ruff linter 통과
- [ ] 타입 힌트가 모두 포함됨
- [ ] docstring이 모든 공개 함수/메서드에 포함됨

### 5.2 문서 완료 기준

- [ ] API 문서가 작성됨
- [ ] README에 사용 예시가 포함됨
- [ ] 환경 변수가 문서화됨
- [ ] CHANGELOG에 항목 추가됨

### 5.3 품질 게이트 통과 기준

- [ ] TRUST 5 프레임워크 준수
  - Test: 85% 커버리지
  - Readable: ruff 통과
  - Unified: black, isort 통과
  - Secured: 보안 취약점 없음
  - Trackable: 명확한 커밋 메시지
- [ ] 모든 수락 기준(AC) 시나리오 통과
- [ ] 에지 케이스 처리 완료
- [ ] 에러 메시지가 명확하고 안내적임

### 5.4 검증 기준

- [ ] 로컬 환경에서 정상 작동
- [ ] 기존 기능(이미지 생성)과 호환
- [ ] 롤백 계획이 문서화됨
- [ ] 성능 기준 충족

---

## 6. 테스트 실행 순서

### 6.1 1차 마일스톤 테스트

```
Phase 1: 핵심 기능
  TC-001 ~ TC-003 (목록 조회)
  TC-004 ~ TC-008 (검색)
  TC-009 ~ TC-010 (상세 조회)
  TC-018 (자동 등록)
```

### 6.2 2차 마일스톤 테스트

```
Phase 2: 삭제 및 정리
  TC-011 ~ TC-014 (삭제)
  TC-015 ~ TC-017 (정리)
  TC-019 ~ TC-020 (일관성)
```

### 6.3 3차 마일스톤 테스트

```
Phase 3: 썸네일 및 고급
  TC-021 ~ TC-024 (썸네일)
  TC-PERF-001 ~ TC-PERF-003 (성능)
  TC-SEC-001 ~ TC-SEC-002 (보안)
  TC-INT-001 ~ TC-INT-002 (무결성)
```

---

## 7. 수락 테스트 실행 가이드

### 7.1 테스트 환경 설정

```bash
# 1. 의존성 설치
pip install pillow pytest pytest-asyncio

# 2. 환경 변수 설정
export GALLERY_THUMBNAILS_ENABLED=true
export GALLERY_METADATA_PATH=output/images/metadata.json

# 3. 테스트 데이터 생성
# (테스트 스크립트로 4개의 이미지 생성)

# 4. 테스트 실행
pytest tests/test_gallery.py -v
```

### 7.2 수동 테스트 체크리스트

```
□ MCP 클라이언트에서 list_images 호출 시 이미지 목록 확인
□ style="cinematic"으로 검색 시 해당 스타일만 반환되는지 확인
□ confirm=True로 delete_image 호출 시 실제 삭제되는지 확인
□ cleanup_old_images dry_run 모드로 예상 삭제 목록 확인
□ 메타데이터 파일이 생성되고 갱신되는지 확인
```

---

## 8. 실패 시 대응

### 8.1 테스트 실패 분석

1. **단위 테스트 실패**: 코드 로직 버그 → 수정 후 재테스트
2. **통합 테스트 실패**: 통합 문제 → 로그 분석 후 수정
3. **성능 테스트 실패**: 최적화 필요 → 프로파일링 후 개선
4. **수락 기준 실패**: 요구사항 불충족 → SPEC 재검토

### 8.2 재검증 기준

- 실패한 테스트 케이스 수정 후 전체 재실행
- 회귀 방지를 위해 통과한 테스트도 재실행
- 버그 수정 후 관련 테스트 추가
