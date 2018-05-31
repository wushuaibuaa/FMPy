# FMI Cross-Check

FMPy provides functions and scripts to help vendors provide test FMUs, import test FMUs of other vendors into their tools and validate their repositories before pushing changes.


## Cloning the Cross-Check Vendor Repositories

Clone or pull all [vendor repositories](https://github.com/orgs/fmi-crosscheck) into the current directory:

```
python -m fmpy.cross_check.clone_vendor_repos
```

Clone or pull `ESI-ITI` and `QTronic` to `D:\fmi-crosscheck`:

```
python -m fmpy.cross_check.clone_vendor_repos --destination D:\fmi-crosscheck --vendors ESI-ITI QTronic
```


## Validating Test FMUs and Cross-Check Results

Validate the current directory:

```
python -m fmpy.cross_check.validate_vendor_repo
```

Validate `D:\fmi-crosscheck\QTronic` and exclude non-compliant test FMUs and cross-check results
by adding `doesNotComplyWithLatestRules` or removing `available` files:

```
python -m fmpy.cross_check.validate_vendor_repo D:\fmi-crosscheck\QTronic --fix-fmus --fix-results
```
