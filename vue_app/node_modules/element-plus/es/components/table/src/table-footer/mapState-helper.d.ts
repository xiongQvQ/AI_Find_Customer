declare function useMapState(): {
    leftFixedLeafCount: import("vue").ComputedRef<number>;
    rightFixedLeafCount: import("vue").ComputedRef<number>;
    columnsCount: import("vue").ComputedRef<number>;
    leftFixedCount: import("vue").ComputedRef<number>;
    rightFixedCount: import("vue").ComputedRef<number>;
    columns: import("vue").ComputedRef<import("element-plus").TableColumnCtx<import("../table/defaults").DefaultRow>[]>;
};
export default useMapState;
