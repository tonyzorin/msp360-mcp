"""Live integration checks for billing/storage usage fixes."""
import asyncio
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "msp360-mcp")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

ABC_ID = "f296cca0-85a7-4be2-97eb-b7f9d4ff3c50"


async def run_tool(name, coro):
    try:
        result = await coro
        if isinstance(result, dict) and result.get("error"):
            print(f"FAIL {name}: {result['error']}")
            return False, result
        print(f"OK   {name}")
        return True, result
    except Exception as exc:
        print(f"FAIL {name}: {type(exc).__name__}: {exc}")
        return False, {"error": str(exc)}


async def main():
    from services.msp360 import get_mbs_client

    client = get_mbs_client()
    passed = 0
    total = 0

    for label, coro in [
        (
            "get_billing_filtered CompanyName=ABC",
            client.get_filtered_billing({"CompanyName": "ABC"}),
        ),
        (
            "get_billing_filtered company_id",
            client.get_filtered_billing({"company_id": ABC_ID}),
        ),
        ("get_company_storage_usage", client.get_company_storage_usage(ABC_ID)),
    ]:
        total += 1
        ok, result = await run_tool(label, coro)
        if ok:
            passed += 1
            if isinstance(result, dict):
                stats = result.get("StatisticBilling") or []
                abc_rows = [
                    r for r in stats if (r.get("CompanyName") or "") == "ABC"
                ]
                print(
                    f"     CurrentSpaceUsed={result.get('CurrentSpaceUsed')} "
                    f"ABC rows={len(abc_rows)}"
                )

    total += 1
    company = await client.get_company(ABC_ID)
    billing = await client.get_company_storage_usage(ABC_ID)
    ok = not (isinstance(billing, dict) and billing.get("error"))
    print(f"{'OK' if ok else 'FAIL'} storage_usage_report (company scope)")
    if ok:
        passed += 1
        name = company.get("Name") if isinstance(company, dict) else None
        keys = list(billing.keys())[:6] if isinstance(billing, dict) else []
        print(f"     company={name} billing keys={keys}")

    print(f"\nRESULT: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    ok = asyncio.run(main())
    raise SystemExit(0 if ok else 1)
