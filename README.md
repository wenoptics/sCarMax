### Usage

```python
from CarmaxBrowser import CarmaxBrowser
from CarmaxAPI import CarmaxAPI

browser = CarmaxBrowser()
api = CarmaxAPI(browser)
records = api.search_model_headless_all(search='/cars?search=camry', zip_code=15206)
browser.close_browser()
```

Also, see [`Prediction.ipynb`](./Prediction.ipynb)