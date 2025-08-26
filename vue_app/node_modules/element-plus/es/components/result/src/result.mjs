import { InfoFilled, CircleCheckFilled, WarningFilled, CircleCloseFilled } from '@element-plus/icons-vue';
import { buildProps } from '../../../utils/vue/props/runtime.mjs';

const IconMap = {
  primary: "icon-primary",
  success: "icon-success",
  warning: "icon-warning",
  error: "icon-error",
  info: "icon-info"
};
const IconComponentMap = {
  [IconMap.primary]: InfoFilled,
  [IconMap.success]: CircleCheckFilled,
  [IconMap.warning]: WarningFilled,
  [IconMap.error]: CircleCloseFilled,
  [IconMap.info]: InfoFilled
};
const resultProps = buildProps({
  title: {
    type: String,
    default: ""
  },
  subTitle: {
    type: String,
    default: ""
  },
  icon: {
    type: String,
    values: ["primary", "success", "warning", "info", "error"],
    default: "info"
  }
});

export { IconComponentMap, IconMap, resultProps };
//# sourceMappingURL=result.mjs.map
