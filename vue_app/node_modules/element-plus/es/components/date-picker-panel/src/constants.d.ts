import type { InjectionKey, SetupContext } from 'vue';
import type { UseNamespaceReturn } from 'element-plus/es/hooks';
interface DatePickerContext {
    slots: SetupContext['slots'];
    pickerNs: UseNamespaceReturn;
}
export declare const ROOT_PICKER_INJECTION_KEY: InjectionKey<DatePickerContext>;
export declare const ROOT_PICKER_IS_DEFAULT_FORMAT_INJECTION_KEY = "ElIsDefaultFormat";
export {};
