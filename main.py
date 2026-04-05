def contractor_card_html(contractor: Dict[str, Any]) -> str:
    contractor_id = contractor.get("id")

    business_name = display_business_name(contractor)
    service = display_service(contractor)
    location = display_location(contractor)
    approved = contractor.get("approved") is True

    badge = (
        '<span class="badge badge-approved">APPROVED</span>'
        if approved else
        '<span class="badge badge-pending">PENDING</span>'
    )

    return f"""
    <a href="/request/{contractor_id}" style="text-decoration:none;color:inherit;">
        <article class="contractor-card">
            <div class="contractor-top">
                <h3 class="contractor-name">{escape(business_name)}</h3>
                {badge}
            </div>
            <div class="meta-list">
                <div class="meta-item"><span class="meta-label">Service:</span> {escape(service)}</div>
                <div class="meta-item"><span class="meta-label">Location:</span> {escape(location)}</div>
            </div>
        </article>
    </a>
    """
