import type { Dayjs } from 'dayjs';
import type { DateModelType, DayOrDays, ModelValueType, PickerOptions, SingleOrRange, UserInput } from '../common/props';
interface CommonPickerProps {
    modelValue: ModelValueType | null;
    valueFormat?: string;
}
type CommonPickerEmits = (event: 'update:modelValue' | 'calendar-change' | 'panel-change', ...args: any[]) => void;
export declare const useCommonPicker: <P extends CommonPickerProps, E extends CommonPickerEmits>(props: P, emit: E) => {
    parsedValue: import("vue").ComputedRef<DayOrDays>;
    pickerActualVisible: import("vue").Ref<boolean>;
    pickerOptions: import("vue").Ref<{
        isValidValue?: ((date: DayOrDays) => boolean) | undefined;
        handleKeydownInput?: ((event: KeyboardEvent) => void) | undefined;
        parseUserInput?: ((value: UserInput) => DayOrDays) | undefined;
        formatToString?: ((value: DayOrDays) => UserInput) | undefined;
        getRangeAvailableTime?: ((date: DayOrDays) => DayOrDays) | undefined;
        getDefaultValue?: (() => DayOrDays) | undefined;
        panelReady?: boolean | undefined;
        handleClear?: (() => void) | undefined;
        handleFocusPicker?: (() => void) | undefined;
    }>;
    pickerVisible: import("vue").Ref<boolean>;
    userInput: import("vue").Ref<UserInput>;
    valueIsEmpty: import("vue").ComputedRef<boolean>;
    emitInput: (input: SingleOrRange<DateModelType> | null) => void;
    onCalendarChange: (e: [Date, null | Date]) => void;
    onPanelChange: (value: [Dayjs, Dayjs], mode: "month" | "year", view: unknown) => void;
    onPick: (date?: any, visible?: boolean) => void;
    onSetPickerOption: <T extends keyof PickerOptions>(e: [T, PickerOptions[T]]) => void;
};
export type CommonPickerContext = ReturnType<typeof useCommonPicker>;
export {};
