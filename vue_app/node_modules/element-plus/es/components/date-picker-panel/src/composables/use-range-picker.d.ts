import dayjs from 'dayjs';
import type { Ref } from 'vue';
import type { Dayjs } from 'dayjs';
import type { PanelRangeSharedProps, RangeState } from '../props/shared';
import type { DefaultValue } from '../utils';
type UseRangePickerProps = {
    onParsedValueChanged: (minDate: Dayjs | undefined, maxDate: Dayjs | undefined) => void;
    defaultValue: Ref<DefaultValue>;
    defaultTime?: Ref<DefaultValue>;
    leftDate: Ref<Dayjs>;
    rightDate: Ref<Dayjs>;
    step?: number;
    unit: 'month' | 'year';
};
export declare const useRangePicker: (props: PanelRangeSharedProps, { defaultValue, defaultTime, leftDate, rightDate, step, unit, onParsedValueChanged, }: UseRangePickerProps) => {
    minDate: Ref<dayjs.Dayjs | undefined>;
    maxDate: Ref<dayjs.Dayjs | undefined>;
    rangeState: Ref<{
        endDate: {
            clone: () => Dayjs;
            isValid: () => boolean;
            year: {
                (): number;
                (value: number): Dayjs;
            };
            month: {
                (): number;
                (value: number): Dayjs;
            };
            date: {
                (): number;
                (value: number): Dayjs;
            };
            day: {
                (): 0 | 1 | 2 | 3 | 4 | 5 | 6;
                (value: number): Dayjs;
            };
            hour: {
                (): number;
                (value: number): Dayjs;
            };
            minute: {
                (): number;
                (value: number): Dayjs;
            };
            second: {
                (): number;
                (value: number): Dayjs;
            };
            millisecond: {
                (): number;
                (value: number): Dayjs;
            };
            set: (unit: dayjs.UnitType, value: number) => Dayjs;
            get: (unit: dayjs.UnitType) => number;
            add: (value: number, unit?: dayjs.ManipulateType) => Dayjs;
            subtract: (value: number, unit?: dayjs.ManipulateType) => Dayjs;
            startOf: (unit: dayjs.OpUnitType) => Dayjs;
            endOf: (unit: dayjs.OpUnitType) => Dayjs;
            format: (template?: string) => string;
            diff: (date?: dayjs.ConfigType, unit?: dayjs.QUnitType | dayjs.OpUnitType, float?: boolean) => number;
            valueOf: () => number;
            unix: () => number;
            daysInMonth: () => number;
            toDate: () => Date;
            toJSON: () => string;
            toISOString: () => string;
            toString: () => string;
            utcOffset: () => number;
            isBefore: (date?: dayjs.ConfigType, unit?: dayjs.OpUnitType) => boolean;
            isSame: (date?: dayjs.ConfigType, unit?: dayjs.OpUnitType) => boolean;
            isAfter: (date?: dayjs.ConfigType, unit?: dayjs.OpUnitType) => boolean;
            locale: {
                (): string;
                (preset: string | ILocale, object?: Partial<ILocale>): Dayjs;
            };
            localeData: () => dayjs.InstanceLocaleDataReturn;
            week: {
                (): number;
                (value: number): Dayjs;
            };
            weekYear: () => number;
            dayOfYear: {
                (): number;
                (value: number): Dayjs;
            };
            isSameOrAfter: (date?: dayjs.ConfigType, unit?: dayjs.OpUnitType) => boolean;
            isSameOrBefore: (date?: dayjs.ConfigType, unit?: dayjs.OpUnitType) => boolean;
        } | null;
        selecting: boolean;
    }>;
    lang: Ref<string>;
    ppNs: {
        namespace: import("vue").ComputedRef<string>;
        b: (blockSuffix?: string) => string;
        e: (element?: string) => string;
        m: (modifier?: string) => string;
        be: (blockSuffix?: string, element?: string) => string;
        em: (element?: string, modifier?: string) => string;
        bm: (blockSuffix?: string, modifier?: string) => string;
        bem: (blockSuffix?: string, element?: string, modifier?: string) => string;
        is: {
            (name: string, state: boolean | undefined): string;
            (name: string): string;
        };
        cssVar: (object: Record<string, string>) => Record<string, string>;
        cssVarName: (name: string) => string;
        cssVarBlock: (object: Record<string, string>) => Record<string, string>;
        cssVarBlockName: (name: string) => string;
    };
    drpNs: {
        namespace: import("vue").ComputedRef<string>;
        b: (blockSuffix?: string) => string;
        e: (element?: string) => string;
        m: (modifier?: string) => string;
        be: (blockSuffix?: string, element?: string) => string;
        em: (element?: string, modifier?: string) => string;
        bm: (blockSuffix?: string, modifier?: string) => string;
        bem: (blockSuffix?: string, element?: string, modifier?: string) => string;
        is: {
            (name: string, state: boolean | undefined): string;
            (name: string): string;
        };
        cssVar: (object: Record<string, string>) => Record<string, string>;
        cssVarName: (name: string) => string;
        cssVarBlock: (object: Record<string, string>) => Record<string, string>;
        cssVarBlockName: (name: string) => string;
    };
    handleChangeRange: (val: RangeState) => void;
    handleRangeConfirm: (visible?: boolean) => void;
    handleShortcutClick: (shortcut: import("./use-shortcut").Shortcut) => void;
    onSelect: (selecting: boolean) => void;
    onReset: (parsedValue: PanelRangeSharedProps["parsedValue"]) => void;
    t: import("element-plus/es/hooks").Translator;
};
export {};
