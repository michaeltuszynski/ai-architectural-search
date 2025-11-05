# Test Queries and Validation Dataset Documentation

## Overview

This document provides comprehensive documentation for the test queries and validation dataset created for the AI Architectural Search System. The test dataset ensures system reliability and accuracy during client demonstrations.

## Requirements Coverage

This test dataset addresses the following requirements:

- **Requirement 5.1**: Successfully process at least 10 predefined test queries with reasonable accuracy
- **Requirement 1.2**: Support queries about building materials (brick, stone, steel, glass)  
- **Requirement 1.3**: Support queries about architectural features (roofs, windows, columns)

## Test Query Categories

### 1. Material-Based Queries (High Priority)

These queries test the system's ability to identify and match building materials:

| Query | Expected Materials | Expected Results | Purpose |
|-------|-------------------|------------------|---------|
| "red brick buildings" | red brick, brick | 2-5 results | Test brick material recognition |
| "stone facades" | stone, limestone, granite, sandstone | 2-5 results | Test stone material identification |
| "glass and steel structures" | glass, steel | 2-5 results | Test modern material combination |
| "concrete buildings" | concrete | 1-5 results | Test concrete material detection |

### 2. Architectural Feature Queries

These queries test recognition of specific architectural elements:

| Query | Expected Features | Expected Results | Purpose |
|-------|------------------|------------------|---------|
| "buildings with large windows" | windows, large windows, glazing | 2-5 results | Test window feature detection |
| "flat roof buildings" | flat roof, modern, commercial | 1-5 results | Test roof type identification |
| "classical columns" | columns, classical, institutional | 1-5 results | Test classical feature recognition |
| "curved architectural elements" | curved, modern, contemporary | 1-5 results | Test geometric feature detection |

### 3. Building Type Queries

These queries test identification of building functions and types:

| Query | Expected Types | Expected Results | Purpose |
|-------|---------------|------------------|---------|
| "residential houses" | residential, house, domestic | 1-5 results | Test residential building identification |
| "office towers" | commercial, tower, office, high-rise | 1-5 results | Test commercial building recognition |
| "institutional buildings" | institutional, civic, government | 1-5 results | Test institutional architecture |

### 4. Mixed Material Queries

These queries test recognition of contemporary mixed-material architecture:

| Query | Expected Materials | Expected Results | Purpose |
|-------|-------------------|------------------|---------|
| "brick and glass combination" | brick, glass | 1-5 results | Test mixed material detection |
| "wood and steel architecture" | wood, steel | 1-5 results | Test sustainable material combinations |

### 5. Complex Descriptive Queries (Demo Showcase)

These queries demonstrate the system's natural language understanding:

| Query | Description | Expected Results | Demo Value |
|-------|-------------|------------------|------------|
| "modern museum with glass facade" | Contemporary cultural buildings | 1-5 results | High - showcases complex understanding |
| "historic brick church" | Traditional religious architecture | 1-5 results | Medium - shows historical recognition |

## Validation Methodology

### Accuracy Metrics

Each test query is validated using multiple criteria:

1. **Result Count Validation**: Ensures results fall within expected range (1-5 images)
2. **Material Match Score**: Percentage of expected materials found in results
3. **Feature Match Score**: Percentage of expected features identified
4. **Category Match Score**: Percentage of expected image categories represented
5. **Overall Accuracy Score**: Weighted average of all validation metrics

### Pass/Fail Criteria

A query passes validation if:
- Result count is within expected range
- At least one expected material is identified
- At least one expected image category is matched
- Overall accuracy score ≥ 0.6 (60%)

### Performance Requirements

- Query processing time must be ≤ 5 seconds
- High priority queries must achieve ≥ 90% pass rate
- Overall system pass rate must be ≥ 80%

## Demo Query Selection

For client demonstrations, the following 8 queries are recommended:

### High Priority Demo Queries (Must Work Perfectly)
1. **"red brick buildings"** - Showcases material recognition
2. **"stone facades"** - Demonstrates classical architecture understanding  
3. **"glass and steel structures"** - Shows modern architecture identification
4. **"buildings with large windows"** - Highlights feature detection
5. **"modern museum with glass facade"** - Complex natural language processing

### Supporting Demo Queries
6. **"residential houses"** - Building type classification
7. **"office towers"** - Commercial architecture recognition
8. **"institutional buildings"** - Civic architecture identification

## Expected Image Distribution

Based on the curated dataset of 45 architectural images:

- **Brick Buildings** (10 images): Traditional and modern brick architecture
- **Glass & Steel** (10 images): Contemporary commercial and institutional buildings  
- **Stone Facades** (10 images): Classical and traditional stone construction
- **Mixed Materials** (15 images): Contemporary mixed-material architecture

## Validation Report Structure

The validation system generates comprehensive reports including:

### Summary Metrics
- Total queries tested
- Pass/fail rates by priority level
- Average accuracy scores
- Performance timing statistics

### Detailed Analysis
- Material recognition accuracy by type
- Feature detection success rates
- Category coverage analysis
- Failed query diagnostics

### Recommendations
- System improvement suggestions
- Performance optimization areas
- Demo preparation guidance

## Usage Instructions

### Running Test Validation

```python
from test_queries_validation import TestQueryDataset, QueryValidator

# Create test dataset
dataset = TestQueryDataset()

# Get demo queries for presentation
demo_queries = dataset.get_demo_queries()

# Validate search results (requires actual search system)
validator = QueryValidator()
results = validator.validate_query_results(query, search_results)
```

### Exporting Demo Queries

```python
# Export queries for demo presentation
dataset.export_queries_for_demo("demo_queries.json")
```

### Coverage Analysis

```python
# Analyze test coverage
coverage = dataset.validate_query_coverage()
print(f"Material coverage: {coverage['material_coverage']}")
print(f"Feature coverage: {coverage['feature_coverage']}")
```

## Integration with Search System

The test queries integrate with the main search system through:

1. **Query Processing**: Each test query is processed through the standard QueryProcessor
2. **Result Validation**: Search results are validated against expected outcomes
3. **Performance Monitoring**: Execution times and accuracy scores are tracked
4. **Demo Preparation**: Validated queries are exported for presentation use

## Maintenance and Updates

### Adding New Queries

To add new test queries:

1. Define query with expected materials, features, and categories
2. Set appropriate priority level (high/normal/low)
3. Validate coverage doesn't create gaps
4. Test with actual search system
5. Update documentation

### Updating Validation Criteria

When modifying validation criteria:

1. Ensure requirements compliance is maintained
2. Test with existing query set
3. Update pass/fail thresholds if needed
4. Document changes and rationale

## Troubleshooting Common Issues

### Low Pass Rates
- Check image metadata quality
- Verify CLIP model performance
- Review similarity thresholds
- Analyze failed query patterns

### Performance Issues
- Monitor query processing times
- Check embedding generation efficiency
- Optimize similarity calculations
- Review result ranking algorithms

### Demo Preparation
- Test all high-priority queries before presentation
- Prepare backup queries for different scenarios
- Verify system performance under demo conditions
- Have troubleshooting steps ready

## Conclusion

This comprehensive test dataset provides robust validation for the AI Architectural Search System, ensuring reliable performance during client demonstrations while maintaining high accuracy standards for architectural image retrieval.