import { getCurrentInstance, inject, unref } from 'vue';
import { computedEager } from '@vueuse/core';
import { useGetDerivedNamespace } from '../use-namespace/index.mjs';

const defaultIdInjection = {
  prefix: Math.floor(Math.random() * 1e4),
  current: 0
};
const ID_INJECTION_KEY = Symbol("elIdInjection");
const useIdInjection = () => {
  return getCurrentInstance() ? inject(ID_INJECTION_KEY, defaultIdInjection) : defaultIdInjection;
};
const useId = (deterministicId) => {
  const idInjection = useIdInjection();
  const namespace = useGetDerivedNamespace();
  const idRef = computedEager(() => unref(deterministicId) || `${namespace.value}-id-${idInjection.prefix}-${idInjection.current++}`);
  return idRef;
};

export { ID_INJECTION_KEY, useId, useIdInjection };
//# sourceMappingURL=index.mjs.map
