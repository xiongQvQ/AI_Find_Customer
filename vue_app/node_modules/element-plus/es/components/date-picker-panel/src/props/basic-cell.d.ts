import type { ExtractPropTypes, __ExtractPublicPropTypes } from 'vue';
import type { DateCell } from '../types';
export declare const basicCellProps: {
    readonly cell: {
        readonly type: import("vue").PropType<DateCell>;
        readonly required: false;
        readonly validator: ((val: unknown) => boolean) | undefined;
        __epPropKey: true;
    };
};
export type BasicCellProps = ExtractPropTypes<typeof basicCellProps>;
export type BasicCellPropsPublic = __ExtractPublicPropTypes<typeof basicCellProps>;
