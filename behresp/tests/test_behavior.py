"""
Tests for functions in behavior.py file.
"""
# CODING-STYLE CHECKS:
# pycodestyle test_behavior.py
# pylint --disable=locally-disabled test_behavior.py

import numpy as np
import pandas as pd
import taxcalc as tc
from behresp import PARAM_INFO, response


def test_param_info():
    """
    Test structure and content of PARAM_INFO dictionary.
    """
    # ensure PARAM_INFO has correct keys
    actkeys = set(PARAM_INFO.keys())
    expkeys = set(['BE_sub', 'BE_inc', 'BE_cg'])
    assert actkeys == expkeys
    for pname in PARAM_INFO:
        pdict = PARAM_INFO[pname]
        # ensure that minimum_value no less than maximum_value
        assert pdict['minimum_value'] <= pdict['maximum_value']
        # ensure that default_value is in [minimum_value,maximum_value] range
        assert pdict['default_value'] >= pdict['minimum_value']
        assert pdict['default_value'] <= pdict['maximum_value']


def test_response_function():
    """
    Test response function.
    """
    # pylint: disable=too-many-locals

    behy_json = """{
    "_BE_sub": {"2018": [0.25]},
    "_BE_inc": {"2018": [-0.1]},
    "_BE_cg": {"2018": [-0.79]}
    }"""
    behy_dict = tc.Calculator.read_json_assumptions(behy_json)
    behy_obj = tc.Behavior()
    behy_obj.update_behavior(behy_dict)

    rec = tc.Records.cps_constructor()
    pol = tc.Policy()
    calc1x = tc.Calculator(records=rec, policy=pol)
    calc1y = tc.Calculator(records=rec, policy=pol)
    refyear = 2020
    pol.implement_reform({refyear: {'_II_em': [1500]}})
    assert not pol.parameter_errors
    calc2x = tc.Calculator(records=rec, policy=pol)
    calc2y = tc.Calculator(records=rec, policy=pol, behavior=behy_obj)
    calc2s = tc.Calculator(records=rec, policy=pol)

    calc1x.advance_to_year(refyear)
    calc2x.advance_to_year(refyear)
    calc1y.advance_to_year(refyear)
    calc2y.advance_to_year(refyear)
    calc2s.advance_to_year(refyear)

    calc2s.calc_all()
    itax2s = round(calc2s.weighted_total('iitax') * 1e-9, 3)

    behx_json = """{
    "BE_sub": {"2018": 0.25},
    "BE_inc": {"2018": -0.1},
    "BE_cg": {"2018": -0.79}
    }"""
    behx_dict = tc.Calculator.read_json_assumptions(behx_json)
    df1, df2 = response(calc1x, calc2x, behx_dict, trace=True)
    itax1x = round((df1['iitax'] * df1['s006']).sum() * 1e-9, 3)
    itax2x = round((df2['iitax'] * df2['s006']).sum() * 1e-9, 3)
    assert np.allclose([itax1x, itax2x], [1413.428, 1359.683])

    calc2y_behv = tc.Behavior.response(calc1y, calc2y, trace=True)
    itax1y = round(calc1y.weighted_total('iitax') * 1e-9, 3)
    itax2y = round(calc2y_behv.weighted_total('iitax') * 1e-9, 3)
    assert np.allclose([itax1x, itax2x], [itax1y, itax2y])

    beh_dict = tc.Calculator.read_json_assumptions('{}')
    df1, df2 = response(calc1x, calc2x, beh_dict)
    itax1n = round((df1['iitax'] * df1['s006']).sum() * 1e-9, 3)
    itax2n = round((df2['iitax'] * df2['s006']).sum() * 1e-9, 3)
    assert np.allclose([itax1n, itax2n], [itax1x, itax2s])

    beh_dict = tc.Calculator.read_json_assumptions(
        '{"BE_inc": {"2018": -0.1}}'
    )
    df1, df2 = response(calc1x, calc2x, beh_dict)
    assert isinstance(df1, pd.DataFrame)
    assert isinstance(df2, pd.DataFrame)
