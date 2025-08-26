import { buildProps, definePropType } from '../../../../utils/vue/props/runtime.mjs';

const alphaSliderProps = buildProps({
  color: {
    type: definePropType(Object),
    required: true
  },
  vertical: Boolean,
  disabled: Boolean
});

export { alphaSliderProps };
//# sourceMappingURL=alpha-slider.mjs.map
