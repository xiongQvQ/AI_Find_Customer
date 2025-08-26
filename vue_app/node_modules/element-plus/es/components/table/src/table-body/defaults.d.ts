import type { PropType } from 'vue';
import type { Store } from '../store';
import type { ColumnCls, ColumnStyle, DefaultRow, Table } from '../table/defaults';
import type { TableOverflowTooltipOptions } from '../util';
interface TableBodyProps<T extends DefaultRow> {
    store: Store<T>;
    stripe?: boolean;
    context: Table<T>;
    rowClassName: ColumnCls<T>;
    rowStyle: ColumnStyle<T>;
    fixed: string;
    highlight: boolean;
    tooltipEffect?: string;
    tooltipOptions?: TableOverflowTooltipOptions;
}
declare const defaultProps: {
    store: {
        required: boolean;
        type: PropType<TableBodyProps<any>["store"]>;
    };
    stripe: BooleanConstructor;
    tooltipEffect: StringConstructor;
    tooltipOptions: {
        type: PropType<TableBodyProps<any>["tooltipOptions"]>;
    };
    context: {
        default: () => {};
        type: PropType<TableBodyProps<any>["context"]>;
    };
    rowClassName: PropType<TableBodyProps<any>["rowClassName"]>;
    rowStyle: PropType<TableBodyProps<any>["rowStyle"]>;
    fixed: {
        type: StringConstructor;
        default: string;
    };
    highlight: BooleanConstructor;
};
export { TableBodyProps };
export default defaultProps;
