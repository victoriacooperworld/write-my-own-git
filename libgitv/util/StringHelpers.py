def toBytes(strVal, encoding='ascii'):
  return strVal.encode(encoding) if isinstance(strVal, str) else strVal