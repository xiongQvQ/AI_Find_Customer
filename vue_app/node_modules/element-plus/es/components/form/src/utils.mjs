import { ref, computed } from 'vue';
import { castArray } from 'lodash-unified';
import { isArray } from '@vue/shared';

function useFormLabelWidth() {
  const potentialLabelWidthArr = ref([]);
  const autoLabelWidth = computed(() => {
    if (!potentialLabelWidthArr.value.length)
      return "0";
    const max = Math.max(...potentialLabelWidthArr.value);
    return max ? `${max}px` : "";
  });
  function getLabelWidthIndex(width) {
    const index = potentialLabelWidthArr.value.indexOf(width);
    if (index === -1 && autoLabelWidth.value === "0") ;
    return index;
  }
  function registerLabelWidth(val, oldVal) {
    if (val && oldVal) {
      const index = getLabelWidthIndex(oldVal);
      potentialLabelWidthArr.value.splice(index, 1, val);
    } else if (val) {
      potentialLabelWidthArr.value.push(val);
    }
  }
  function deregisterLabelWidth(val) {
    const index = getLabelWidthIndex(val);
    if (index > -1) {
      potentialLabelWidthArr.value.splice(index, 1);
    }
  }
  return {
    autoLabelWidth,
    registerLabelWidth,
    deregisterLabelWidth
  };
}
const filterFields = (fields, props) => {
  const normalized = castArray(props).map((prop) => isArray(prop) ? prop.join(".") : prop);
  return normalized.length > 0 ? fields.filter((field) => field.propString && normalized.includes(field.propString)) : fields;
};

export { filterFields, useFormLabelWidth };
//# sourceMappingURL=utils.mjs.map
