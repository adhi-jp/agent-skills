export type InventoryItem = {
  sku: string;
  name: string;
  quantity: number;
  warehouse: string;
};

export const visibleInventoryColumns = ["SKU", "Name", "Quantity", "Warehouse"] as const;

export function InventoryTable({ items }: { items: InventoryItem[] }) {
  return (
    <table>
      <thead>
        <tr>
          {visibleInventoryColumns.map((column) => (
            <th key={column}>{column}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.sku}>
            <td>{item.sku}</td>
            <td>{item.name}</td>
            <td>{item.quantity}</td>
            <td>{item.warehouse}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
