import { ref, watch, provide, computed } from 'vue';
import { collapseContextKey } from './constants.mjs';
import { castArray } from 'lodash-unified';
import { UPDATE_MODEL_EVENT, CHANGE_EVENT } from '../../../constants/event.mjs';
import { useNamespace } from '../../../hooks/use-namespace/index.mjs';
import { isPromise } from '@vue/shared';
import { isBoolean } from '../../../utils/types.mjs';
import { throwError } from '../../../utils/error.mjs';

const SCOPE = "ElCollapse";
const useCollapse = (props, emit) => {
  const activeNames = ref(castArray(props.modelValue));
  const setActiveNames = (_activeNames) => {
    activeNames.value = _activeNames;
    const value = props.accordion ? activeNames.value[0] : activeNames.value;
    emit(UPDATE_MODEL_EVENT, value);
    emit(CHANGE_EVENT, value);
  };
  const handleChange = (name) => {
    if (props.accordion) {
      setActiveNames([activeNames.value[0] === name ? "" : name]);
    } else {
      const _activeNames = [...activeNames.value];
      const index = _activeNames.indexOf(name);
      if (index > -1) {
        _activeNames.splice(index, 1);
      } else {
        _activeNames.push(name);
      }
      setActiveNames(_activeNames);
    }
  };
  const handleItemClick = async (name) => {
    const { beforeCollapse } = props;
    if (!beforeCollapse) {
      handleChange(name);
      return;
    }
    const shouldChange = beforeCollapse(name);
    const isPromiseOrBool = [
      isPromise(shouldChange),
      isBoolean(shouldChange)
    ].includes(true);
    if (!isPromiseOrBool) {
      throwError(SCOPE, "beforeCollapse must return type `Promise<boolean>` or `boolean`");
    }
    if (isPromise(shouldChange)) {
      shouldChange.then((result) => {
        if (result !== false) {
          handleChange(name);
        }
      }).catch((e) => {
      });
    } else if (shouldChange) {
      handleChange(name);
    }
  };
  watch(() => props.modelValue, () => activeNames.value = castArray(props.modelValue), { deep: true });
  provide(collapseContextKey, {
    activeNames,
    handleItemClick
  });
  return {
    activeNames,
    setActiveNames
  };
};
const useCollapseDOM = (props) => {
  const ns = useNamespace("collapse");
  const rootKls = computed(() => [
    ns.b(),
    ns.b(`icon-position-${props.expandIconPosition}`)
  ]);
  return {
    rootKls
  };
};

export { useCollapse, useCollapseDOM };
//# sourceMappingURL=use-collapse.mjs.map
