# twitter scrapper

minimal script to search for tweets

# install

No install is required, other than a working python3 installation. Using a virtualenv is encouraged.

```
git clone https://github.com/CrossNox/python-twitter-scrapper.git
cd python-twitter-scrapper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scrapper.py -h
```

# usage

please check usage with
```
python scrapper.py -h
```

# keys
check `keys_sample.yaml` for required keys

## how do i get my keys?
follow [this guide](https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html) to obtain keys for your twitter app

# TODO
* database saving
* allow for specific fields
