# VoiceLLAMA Enhancement Plan

## Overview
This document outlines the plan for enhancing VoiceLLAMA with expanded test coverage, performance benchmarks, API versioning, and real Kokoro integration tests.

---

## 1. Expand Test Coverage

### 1.1 Edge Cases for TTS Endpoints

#### Text Input Edge Cases
- [x] Empty string (already tested)
- [ ] Whitespace-only strings
- [ ] Maximum length text (10000 characters)
- [ ] Text exceeding max length (10001+ characters)
- [ ] Special characters (Unicode, emojis, symbols)
- [ ] Null characters (\x00)
- [ ] Newlines and control characters
- [ ] Very short text (1 character)
- [ ] Text with HTML/XML tags
- [ ] Text with markdown formatting

#### Voice Edge Cases
- [x] Invalid voice (already tested)
- [ ] Empty voice string
- [ ] Voice with whitespace
- [ ] All available voices (test each one)

#### Speed Edge Cases
- [x] Speed too high (already tested)
- [ ] Speed too low (< 0.25)
- [ ] Speed at boundaries (0.25, 3.0)
- [ ] Speed with many decimal places
- [ ] Negative speed values

#### Format Edge Cases
- [ ] Invalid format string
- [ ] Format case sensitivity
- [ ] Format with whitespace
- [ ] Unsupported format (if ffmpeg unavailable)

#### Cache Edge Cases
- [ ] Cache disabled scenario
- [ ] Cache miss after clear
- [ ] Cache hit with different parameters
- [ ] Cache with very large audio files

### 1.2 Batch TTS Edge Cases
- [x] Empty list (already tested)
- [x] Too many items (already tested)
- [ ] Single item batch
- [ ] Maximum items (10)
- [ ] Mixed success/error scenarios
- [ ] All items cached
- [ ] All items errors
- [ ] Partial cache hits

### 1.3 Settings Edge Cases
- [ ] Speed boundary values (0.25, 3.0)
- [ ] Invalid chatter level
- [ ] Custom states validation
- [ ] Settings file corruption
- [ ] Concurrent settings updates

### 1.4 Error Scenarios
- [ ] Pipeline loading failure
- [ ] Pipeline generation failure
- [ ] Cache corruption
- [ ] Queue full scenario
- [ ] Network timeout simulation
- [ ] Memory pressure scenarios

---

## 2. Performance Benchmarks

### 2.1 TTS Generation Latency
- [ ] Single request latency
- [ ] Batch request latency
- [ ] Cached vs uncached comparison
- [ ] Different text lengths
- [ ] Different voice speeds
- [ ] Different output formats

### 2.2 Cache Performance
- [ ] Cache hit rate measurement
- [ ] Cache miss penalty
- [ ] Cache eviction performance
- [ ] Memory usage tracking

### 2.3 Concurrent Request Handling
- [ ] Sequential vs concurrent requests
- [ ] Queue behavior under load
- [ ] Rate limiting effectiveness
- [ ] WebSocket concurrent connections
- [ ] Memory usage under load

### 2.4 Benchmark Framework
- [ ] Use pytest-benchmark
- [ ] Create benchmark fixtures
- [ ] Add benchmark CI job
- [ ] Track performance over time

---

## 3. API Versioning

### 3.1 Version Structure
- [ ] Add `/v1/` prefix to all routes
- [ ] Keep `/` routes for backward compatibility (deprecated)
- [ ] Version header support (`Accept: application/vnd.voicellama.v1+json`)
- [ ] Version in response headers

### 3.2 Versioned Models
- [ ] Create `v1` namespace for models
- [ ] Versioned response models
- [ ] Backward compatibility layer
- [ ] Version migration guide

### 3.3 Documentation
- [ ] Update API docs with versioning
- [ ] Deprecation notices
- [ ] Migration examples
- [ ] Version changelog

---

## 4. Real Kokoro Integration Tests

### 4.1 Test Infrastructure
- [ ] Skip tests if Kokoro not available
- [ ] Environment variable to enable real tests
- [ ] Mock vs real test separation
- [ ] Test data preparation

### 4.2 Integration Test Cases
- [ ] Real TTS generation
- [ ] All voice options
- [ ] Different speeds
- [ ] Different formats
- [ ] Error handling with real pipeline
- [ ] Performance with real model

### 4.3 CI Integration
- [ ] Optional Kokoro installation in CI
- [ ] Mark tests appropriately
- [ ] Conditional test execution

---

## Implementation Order

1. **Phase 1: Expand Test Coverage** (Priority: High)
   - Edge cases for TTS endpoints
   - Error scenarios
   - Settings edge cases

2. **Phase 2: Performance Benchmarks** (Priority: Medium)
   - Benchmark framework setup
   - TTS latency benchmarks
   - Cache performance tests

3. **Phase 3: API Versioning** (Priority: Medium)
   - Version structure implementation
   - Versioned models
   - Documentation updates

4. **Phase 4: Real Kokoro Tests** (Priority: Low)
   - Test infrastructure
   - Integration test cases
   - CI integration

---

## Success Criteria

- [ ] Test coverage > 85%
- [ ] All edge cases covered
- [ ] Performance benchmarks documented
- [ ] API versioning implemented
- [ ] Real Kokoro tests working
- [ ] CI passes all tests
- [ ] Documentation updated

---

## Timeline Estimate

- **Phase 1**: 2-3 hours
- **Phase 2**: 2-3 hours
- **Phase 3**: 2-3 hours
- **Phase 4**: 1-2 hours

**Total**: ~8-11 hours

