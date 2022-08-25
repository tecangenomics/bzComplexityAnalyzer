# bzComplexityAnalyzer

## Getting Started

```python
import bzComplexityAnalyzer
```

## Preparing an analyzer object

```python
analyzer = bzComplexityAnalyzer.Analyzer(alphabet="dna", ignoreCase=True, iterations=1000)
```
- *alphabet:* string or list of characters  Specifies the alphabet to be compared against. Default: DNA
- *ignoreCase:* boolean  If true, casing of letters will be homogenized before analysis to neutralize their effects on complexity
- *iterations* int  Number of random sequences to use for finding the distribution of compressed product lengths

## Estimating the complexity of a sequence

```python
analyzer.getCompressionZScore("GAATTCGAATTCGAATTC") # Returns a Z-score
analyzer.getCompressionPercentile("GAATTCGAATTCGAATTC") # Returns a percentile
```

