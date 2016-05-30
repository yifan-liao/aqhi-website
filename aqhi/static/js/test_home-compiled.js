"use strict";

describe("getAqhiLvel function", function () {

  var testLevel = [['0.8', '3.9'], ['4.0', '6.9'], ['7.0', '7.9'], ['8.0', '10.9'], ['11.0', '15.444']];

  testLevel.forEach(function (args, i) {
    it(`should give level ${ i } when given ${ args.join(', ') }`, function () {
      for (let v of args) expect(getAqhiLevel(v)).toBe(i);
    });
  });
});

describe("parsePollutantOrAqiValue function", function () {

  it('should give 0.21 when given aqhi and 0.2134', function () {
    expect(parsePollutantOrAqiValue('aqhi', '0.2134')).toBe(0.21);
  });
});

//# sourceMappingURL=test_home-compiled.js.map