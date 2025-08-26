import type { PanelDateRangeProps } from '../props/panel-date-range';
import type { Dayjs } from 'dayjs';
import type { ComputedRef, Ref } from 'vue';
type CurrentView = 'date' | 'year' | 'month';
type CurrentViewRef = {
    focus: () => void;
};
export type Emits = (event: 'pick' | 'set-picker-option' | 'calendar-change' | 'panel-change', ...args: any[]) => void;
export declare const usePanelDateRange: (props: PanelDateRangeProps, emit: Emits, leftDate: Ref<Dayjs>, rightDate: Ref<Dayjs>) => {
    leftCurrentView: Ref<CurrentView>;
    rightCurrentView: Ref<CurrentView>;
    leftCurrentViewRef: Ref<CurrentViewRef | undefined>;
    rightCurrentViewRef: Ref<CurrentViewRef | undefined>;
    leftYear: ComputedRef<number>;
    rightYear: ComputedRef<number>;
    leftMonth: ComputedRef<number>;
    rightMonth: ComputedRef<number>;
    leftYearLabel: ComputedRef<string>;
    rightYearLabel: ComputedRef<string>;
    showLeftPicker: (view: "month" | "year") => Promise<void>;
    showRightPicker: (view: "month" | "year") => Promise<void>;
    handleLeftYearPick: (year: number) => Promise<void>;
    handleRightYearPick: (year: number) => Promise<void>;
    handleLeftMonthPick: (month: number) => Promise<void>;
    handleRightMonthPick: (month: number) => Promise<void>;
    handlePanelChange: (mode: "month" | "year") => void;
    adjustDateByView: (currentView: CurrentView, date: Dayjs, forward: boolean) => Dayjs;
};
export {};
