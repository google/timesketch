## Community contributed analyzers

This directory hosts community contributed analyzers. They are not maintained
by the core Timesketch development team. Code in `/contrib/` directories won't
be taken into account in any end-to-end tests run by the core Timesketch 
development team; it's up to contributors to make sure that their code is
properly end-to-end tested.

### For developers

If you require a dependency that is not part of the core Timesketch system
you need to add it to the `contrib_requirements.txt` file in this directory.

In order to support extra dependencies you need to catch any import errors
in your code. For example:

```python
has_required_deps = True
try:
    from google.cloud import bigquery
except ImportError:
    has_required_deps = False

... <your analyzer code here> ...

# Only register the module if all dependencies can be imported
if has_required_deps:
    manager.AnalysisManager.register_analyzer(TestContrib)
```
