import { reactive, watch } from 'vue';
import Color from '../utils/color.mjs';
import { UPDATE_MODEL_EVENT } from '../../../../constants/event.mjs';

const useCommonColor = (props, emit) => {
  const color = reactive(new Color({
    enableAlpha: props.showAlpha,
    format: props.colorFormat || "",
    value: props.modelValue
  }));
  watch(() => [props.colorFormat, props.showAlpha], () => {
    color.enableAlpha = props.showAlpha;
    color.format = props.colorFormat || color.format;
    color.doOnChange();
    emit(UPDATE_MODEL_EVENT, color.value);
  });
  return {
    color
  };
};

export { useCommonColor };
//# sourceMappingURL=use-common-color.mjs.map
