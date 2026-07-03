from io import StringIO
import csv


def transactions_to_csv(transactions: list[dict[str, object]]) -> str:
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Type", "Category / Source", "Description", "Amount"])

    for item in transactions:
        writer.writerow(
            [
                item["date"].strftime("%Y-%m-%d"),
                item["type"],
                item["category"],
                item.get("description") or "",
                f"{item['amount']:.2f}",
            ]
        )

    return output.getvalue()
