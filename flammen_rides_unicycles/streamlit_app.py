"""Streamlit web interface for the Flammen Rides unicycle configurator."""

import streamlit as st

from dictionaries import (
    AVAILABLE_RIM_COLORS,
    BRAKE_OPTIONS,
    CLAMP_COLORS,
    CLAMP_STYLES,
    CRANK_OPTIONS,
    PEDAL_OPTIONS,
    RIM_OPTIONS,
    SADDLE_CUSHION_COLORS,
    SADDLE_LEATHER_COLORS,
    SADDLE_OPTIONS,
    SEAT_POST_OPTIONS,
    TIRE_OPTIONS,
    UNICYCLE_BRANDS,
)
from main import format_invoice
from order_storage import create_order, generate_invoice_number
from pos_defaults import (
    BASE_PRICE,
    EMAIL_PATTERN,
    SHIPPING_METHODS,
    US_STATE_CODES,
    ZIP_CODE_PATTERN,
)

st.set_page_config(page_title="Flammen Rides Unicycles", page_icon="🚲", layout="wide")


def _option_index(options, value):
    """Return a saved option's index, or the first option when it is unavailable."""
    try:
        return options.index(value)
    except ValueError:
        return 0


def _save_build(section):
    st.session_state["draft_order"] = {
        **st.session_state.get("draft_order", {}),
        **section,
    }


def _render_frame_step(draft):
    st.header("Choose your frame and tire")
    st.caption("Start with a frame. Tire choices will be limited to its wheel size.")

    brands = list(UNICYCLE_BRANDS)
    frame_brand = st.selectbox(
        "Frame brand",
        brands,
        index=_option_index(brands, draft.get("frame_brand")),
        key="frame_brand",
    )
    models = UNICYCLE_BRANDS[frame_brand]
    model_names = list(models)
    selected_model = st.selectbox(
        "Model",
        model_names,
        format_func=lambda model: (
            f"{model} ({models[model]['wheel_size']} wheel)"
        ),
        index=_option_index(model_names, draft.get("selected_model")),
        key=f"model_{frame_brand}",
    )
    wheel_size = models[selected_model]["wheel_size"]

    compatible_tires = {
        brand: [
            size
            for size in sizes
            if f'{size.split()[0]}"' == wheel_size
        ]
        for brand, sizes in TIRE_OPTIONS.items()
    }
    compatible_tires = {
        brand: sizes for brand, sizes in compatible_tires.items() if sizes
    }
    if not compatible_tires:
        st.error(f"No tires are available for wheel size {wheel_size}.")
        st.stop()

    saved_tire = draft.get("tire", "")
    saved_tire_brand = next(
        (
            brand
            for brand in compatible_tires
            if saved_tire.startswith(f"{brand} ")
        ),
        None,
    )
    saved_tire_size = (
        saved_tire[len(saved_tire_brand) + 1 :]
        if saved_tire_brand is not None
        else None
    )

    col1, col2 = st.columns(2)
    with col1:
        tire_brands = list(compatible_tires)
        tire_brand = st.selectbox(
            "Tire brand",
            tire_brands,
            index=_option_index(tire_brands, saved_tire_brand),
            key=f"tire_brand_{wheel_size}",
        )
    with col2:
        tire_sizes = compatible_tires[tire_brand]
        tire_size = st.selectbox(
            "Tire size",
            tire_sizes,
            index=_option_index(tire_sizes, saved_tire_size),
            key=f"tire_size_{wheel_size}_{tire_brand}",
        )

    return {
        "frame_brand": frame_brand,
        "selected_model": selected_model,
        "wheel_size": wheel_size,
        "tire": f"{tire_brand} {tire_size}",
    }


def _render_saddle_step(draft):
    st.header("Choose your saddle and seatpost")
    st.caption(
        f"Build for {draft['selected_model']} ({draft['wheel_size']}). "
        "Seatpost choices reflect frame and saddle compatibility."
    )

    saved_saddle = draft.get("saddle", {})
    saved_post = draft.get("seat_post", {})
    col1, col2 = st.columns(2)
    with col1:
        saddle_names = list(SADDLE_OPTIONS)
        saddle_name = st.selectbox(
            "Saddle",
            saddle_names,
            index=_option_index(saddle_names, saved_saddle.get("saddle_name")),
        )
        saddle_specs = SADDLE_OPTIONS[saddle_name]
        cushion_widths = saddle_specs["cushion_widths"]
        saddle_width = st.selectbox(
            "Cushion width",
            cushion_widths,
            index=_option_index(cushion_widths, saved_saddle.get("width")),
        )
        cushion_color = st.selectbox(
            "Cushion color",
            SADDLE_CUSHION_COLORS,
            index=_option_index(
                SADDLE_CUSHION_COLORS,
                saved_saddle.get("cushion_color"),
            ),
        )
        leather_color = "N/A"
        if saddle_specs.get("handle_leather_option", False):
            saved_leather = saved_saddle.get("leather_color", "N/A")
            customize_leather = st.checkbox(
                "Add custom handle leather",
                value=saved_leather != "N/A",
            )
            if customize_leather:
                leather_color = st.selectbox(
                    "Handle leather color",
                    SADDLE_LEATHER_COLORS,
                    index=_option_index(SADDLE_LEATHER_COLORS, saved_leather),
                )

    compatible_posts = [
        name
        for name, specs in SEAT_POST_OPTIONS.items()
        if draft["frame_brand"] in specs.get("compatible_brands", [])
        or specs.get("type", "Standard")
        == saddle_specs.get("mount_style", "Standard")
    ]
    if not compatible_posts:
        st.error(f"No compatible seatposts are available for {draft['frame_brand']}.")
        st.stop()

    with col2:
        post_name = st.selectbox(
            "Seatpost",
            compatible_posts,
            index=_option_index(compatible_posts, saved_post.get("post_model")),
        )
        post_specs = SEAT_POST_OPTIONS[post_name]
        post_lengths = post_specs.get("lengths_mm", [300])
        post_length = st.selectbox(
            "Seatpost length (mm)",
            post_lengths,
            index=_option_index(post_lengths, saved_post.get("length_mm")),
        )
        clamp_names = list(CLAMP_STYLES)
        clamp_name = st.selectbox(
            "Seatpost clamp",
            clamp_names,
            index=_option_index(clamp_names, saved_post.get("clamp_style")),
        )
        clamp_color = "Standard Black"
        if CLAMP_STYLES[clamp_name].get("color_customizable", False):
            clamp_color = st.selectbox(
                "Clamp color",
                CLAMP_COLORS,
                index=_option_index(CLAMP_COLORS, saved_post.get("clamp_color")),
            )

    return {
        "saddle": {
            "saddle_name": saddle_name,
            "mount_style": saddle_specs.get("mount_style", "Standard"),
            "width": saddle_width,
            "cushion_color": cushion_color,
            "leather_color": leather_color,
        },
        "seat_post": {
            "post_model": post_name,
            "diameter_mm": post_specs.get("diameter_mm"),
            "length_mm": post_length,
            "clamp_style": clamp_name,
            "clamp_color": clamp_color,
        },
    }


def _render_drivetrain_step(draft):
    st.header("Choose your rim, drivetrain, and brakes")
    st.caption(f"Component options are based on your {draft['wheel_size']} frame.")

    saved_rim = draft.get("rim", {})
    saved_cranks = draft.get("cranks", {})
    saved_pedals = draft.get("pedals", {})
    saved_brakes = draft.get("brakes", {})

    compatible_rims = [
        name
        for name, specs in RIM_OPTIONS.items()
        if draft["wheel_size"] in specs.get("compatible_wheel_sizes", [])
    ]
    if not compatible_rims:
        st.error(f"No rims are available for wheel size {draft['wheel_size']}.")
        st.stop()

    col1, col2 = st.columns(2)
    with col1:
        rim_name = st.selectbox(
            "Rim",
            compatible_rims,
            index=_option_index(compatible_rims, saved_rim.get("rim_model")),
        )
        rim_color = st.selectbox(
            "Rim color",
            AVAILABLE_RIM_COLORS,
            index=_option_index(AVAILABLE_RIM_COLORS, saved_rim.get("rim_color")),
        )
        rim_specs = RIM_OPTIONS[rim_name]

        crank_names = list(CRANK_OPTIONS)
        crank_name = st.selectbox(
            "Crank model",
            crank_names,
            index=_option_index(crank_names, saved_cranks.get("crank_model")),
        )
        crank_specs = CRANK_OPTIONS[crank_name]
        crank_lengths = crank_specs.get("lengths", ["125mm"])
        crank_length = st.selectbox(
            "Crank length",
            crank_lengths,
            index=_option_index(crank_lengths, saved_cranks.get("length")),
        )
        crank_colors = crank_specs.get("available_colors", ["Black"])
        crank_color = st.selectbox(
            "Crank color",
            crank_colors,
            index=_option_index(crank_colors, saved_cranks.get("color")),
        )

    with col2:
        pedal_brands = list(PEDAL_OPTIONS)
        pedal_brand = st.selectbox(
            "Pedal brand",
            pedal_brands,
            index=_option_index(pedal_brands, saved_pedals.get("pedal_brand")),
        )
        pedal_specs = PEDAL_OPTIONS[pedal_brand]
        pedal_colors = pedal_specs.get("available_colors", ["Black"])
        pedal_color = st.selectbox(
            "Pedal color",
            pedal_colors,
            index=_option_index(pedal_colors, saved_pedals.get("color")),
        )

        brake_data = {
            "brakes_installed": False,
            "brake_model": "None",
            "type": "N/A",
            "rotor_diameter_mm": "N/A",
        }
        model_specs = UNICYCLE_BRANDS[draft["frame_brand"]][draft["selected_model"]]
        brakes_installed = False
        if model_specs.get("disc_brakes_supported", True):
            brakes_installed = st.checkbox(
                "Install brakes",
                value=saved_brakes.get("brakes_installed", True),
            )
        else:
            st.info("This frame does not support disc brakes.")

        if brakes_installed:
            brake_names = list(BRAKE_OPTIONS)
            brake_name = st.selectbox(
                "Brake system",
                brake_names,
                index=_option_index(brake_names, saved_brakes.get("brake_model")),
            )
            brake_specs = BRAKE_OPTIONS[brake_name]
            supported_rotors = brake_specs.get("supported_rotors_mm", [])
            rotor_size = "N/A"
            if supported_rotors:
                default_rotor = saved_brakes.get(
                    "rotor_diameter_mm",
                    brake_specs.get("default_rotor_mm"),
                )
                if default_rotor not in supported_rotors:
                    default_rotor = brake_specs.get("default_rotor_mm")
                rotor_size = st.selectbox(
                    "Rotor size (mm)",
                    supported_rotors,
                    index=_option_index(supported_rotors, default_rotor),
                )
            brake_data = {
                "brakes_installed": True,
                "brake_model": brake_name,
                "type": brake_specs.get("type", "Hydraulic Disc"),
                "rotor_diameter_mm": rotor_size,
            }

    return {
        "rim": {
            "rim_model": rim_name,
            "rim_color": rim_color,
            "width_mm": rim_specs.get("width_mm", "Standard"),
            "construction": rim_specs.get("construction", "double-wall"),
        },
        "cranks": {
            "crank_model": crank_name,
            "interface": crank_specs.get("interface", "Standard"),
            "length": crank_length,
            "color": crank_color,
        },
        "pedals": {
            "pedal_brand": pedal_brand,
            "material": pedal_specs.get("material", "Plastic platform"),
            "pins": pedal_specs.get("pins", "Molded studs"),
            "color": pedal_color,
        },
        "brakes": brake_data,
    }


def _render_build_review(order_data):
    st.header("Review your build")
    st.caption("Billing and shipping details come after you confirm this configuration.")
    st.markdown(
        f"**Frame:** {order_data['frame_brand']} — {order_data['selected_model']} "
        f"({order_data['wheel_size']})"
    )
    st.markdown(f"**Tire:** {order_data['tire']}")

    with st.expander("Component details", expanded=True):
        saddle = order_data["saddle"]
        post = order_data["seat_post"]
        rim = order_data["rim"]
        cranks = order_data["cranks"]
        pedals = order_data["pedals"]
        brakes = order_data["brakes"]
        st.write(
            f"**Saddle:** {saddle['saddle_name']} — {saddle['width']} cushion, "
            f"{saddle['cushion_color']} (handle leather: {saddle['leather_color']})"
        )
        st.write(
            f"**Seatpost:** {post['post_model']}, {post['length_mm']} mm — "
            f"{post['clamp_style']} ({post['clamp_color']})"
        )
        st.write(f"**Rim:** {rim['rim_model']} — {rim['rim_color']}")
        st.write(
            f"**Cranks:** {cranks['crank_model']} — {cranks['length']}, "
            f"{cranks['color']}"
        )
        st.write(
            f"**Pedals:** {pedals['pedal_brand']} — {pedals['color']} "
            f"({pedals['material']})"
        )
        brake_summary = (
            f"{brakes['brake_model']} ({brakes['rotor_diameter_mm']} mm rotor)"
            if brakes["brakes_installed"]
            else "Not installed"
        )
        st.write(f"**Brakes:** {brake_summary}")

    tax_amount = BASE_PRICE * 0.08
    before_shipping = BASE_PRICE + tax_amount
    price_col1, price_col2 = st.columns(2)
    price_col1.metric("Build subtotal", f"${BASE_PRICE:.2f}")
    price_col2.metric("Estimated total before shipping", f"${before_shipping:.2f}")
    st.caption("Shipping is selected during checkout and added to the final invoice.")

    edit_cols = st.columns(3)
    edit_steps = (
        ("Edit frame & tire", "frame"),
        ("Edit saddle & seatpost", "saddle"),
        ("Edit rim & drivetrain", "drivetrain"),
    )
    for column, (label, step) in zip(edit_cols, edit_steps):
        if column.button(label):
            st.session_state["flow_step"] = step
            st.rerun()

    if st.button("Confirm build and continue to billing & shipping", type="primary"):
        st.session_state["flow_step"] = "checkout"
        st.rerun()


def _checkout_errors(billing, shipping):
    errors = []
    if not billing["full_name"]:
        errors.append("Enter the billing name.")
    if not EMAIL_PATTERN.fullmatch(billing["email"]):
        errors.append("Enter a valid email address.")
    if not billing["address"] or not billing["city"]:
        errors.append("Enter the billing street address and city.")
    if billing["state"] not in US_STATE_CODES:
        errors.append("Enter a valid two-letter billing state code.")
    if not ZIP_CODE_PATTERN.fullmatch(billing["zip_code"]):
        errors.append("Enter a valid billing ZIP code.")
    if any(not value for value in shipping["destination"].values()):
        errors.append("Complete all shipping address fields.")
    if shipping["destination"]["state"] not in US_STATE_CODES:
        errors.append("Enter a valid two-letter shipping state code.")
    if not ZIP_CODE_PATTERN.fullmatch(shipping["destination"]["zip_code"]):
        errors.append("Enter a valid shipping ZIP code.")
    return errors


def _render_checkout(order_data):
    checkout_draft = st.session_state.get("checkout_draft", {})
    saved_billing = checkout_draft.get("billing", {})
    saved_destination = checkout_draft.get("destination", {})

    st.header("Billing and shipping")
    st.caption("Your build is confirmed. Complete these details to place the order.")
    st.markdown(
        f"**Confirmed build:** {order_data['frame_brand']} — "
        f"{order_data['selected_model']} ({order_data['wheel_size']})"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Billing information")
        billing = {
            "full_name": st.text_input(
                "Full name",
                value=saved_billing.get("full_name", ""),
                key="billing_name",
            ).strip(),
            "email": st.text_input(
                "Email",
                value=saved_billing.get("email", ""),
                key="billing_email",
            ).strip(),
            "address": st.text_input(
                "Street address",
                value=saved_billing.get("address", ""),
                key="billing_address",
            ).strip(),
            "city": st.text_input(
                "City",
                value=saved_billing.get("city", ""),
                key="billing_city",
            ).strip(),
            "state": st.text_input(
                "State (2-letter code)",
                value=saved_billing.get("state", ""),
                max_chars=2,
                key="billing_state",
            ).strip().upper(),
            "zip_code": st.text_input(
                "ZIP code",
                value=saved_billing.get("zip_code", ""),
                key="billing_zip",
            ).strip(),
        }
        payment_methods = ["Credit Card", "PayPal", "Apple Pay"]
        payment_method = st.selectbox(
            "Payment method",
            payment_methods,
            index=_option_index(
                payment_methods,
                checkout_draft.get("payment_method"),
            ),
            help="This prototype records your selection but does not process payments.",
            key="payment_method",
        )
        billing["payment_method"] = payment_method

    with col2:
        st.subheader("Shipping information")
        same_as_billing = st.checkbox(
            "Use billing address for shipping",
            value=checkout_draft.get("same_as_billing", True),
            key="same_as_billing",
        )
        if same_as_billing:
            destination = {
                "full_name": billing["full_name"],
                "address": billing["address"],
                "city": billing["city"],
                "state": billing["state"],
                "zip_code": billing["zip_code"],
            }
        else:
            destination = {
                "full_name": st.text_input(
                    "Recipient full name",
                    value=saved_destination.get("full_name", ""),
                    key="shipping_name",
                ).strip(),
                "address": st.text_input(
                    "Shipping street address",
                    value=saved_destination.get("address", ""),
                    key="shipping_address",
                ).strip(),
                "city": st.text_input(
                    "Shipping city",
                    value=saved_destination.get("city", ""),
                    key="shipping_city",
                ).strip(),
                "state": st.text_input(
                    "Shipping state (2-letter code)",
                    value=saved_destination.get("state", ""),
                    max_chars=2,
                    key="shipping_state",
                ).strip().upper(),
                "zip_code": st.text_input(
                    "Shipping ZIP code",
                    value=saved_destination.get("zip_code", ""),
                    key="shipping_zip",
                ).strip(),
            }

        shipping_choices = list(SHIPPING_METHODS)
        shipping_choice = st.selectbox(
            "Shipping method",
            shipping_choices,
            index=_option_index(
                shipping_choices,
                checkout_draft.get("shipping_choice"),
            ),
            format_func=lambda choice: (
                f"{SHIPPING_METHODS[choice]['name']} — "
                f"${SHIPPING_METHODS[choice]['cost']:.2f} "
                f"({SHIPPING_METHODS[choice]['days']})"
            ),
            key="shipping_choice",
        )

    shipping_specs = SHIPPING_METHODS[shipping_choice]
    shipping = {
        "destination": destination,
        "method_name": shipping_specs["name"],
        "shipping_cost": shipping_specs["cost"],
        "delivery_estimate": shipping_specs["days"],
    }
    order_data = {
        **order_data,
        "billing": billing,
        "shipping": shipping,
    }
    shipping_cost = shipping_specs["cost"]
    tax_amount = BASE_PRICE * 0.08
    total_cost = BASE_PRICE + tax_amount + shipping_cost

    st.subheader("Final order review")
    price_col1, price_col2, price_col3 = st.columns(3)
    price_col1.metric("Build subtotal", f"${BASE_PRICE:.2f}")
    price_col2.metric("Estimated tax (8%)", f"${tax_amount:.2f}")
    price_col3.metric("Total with shipping", f"${total_cost:.2f}")
    st.code(
        format_invoice(order_data, "PREVIEW", BASE_PRICE, tax_amount, total_cost),
        language=None,
    )

    confirmed = st.checkbox("I have reviewed the order and want to submit it.")
    edit_col, submit_col = st.columns(2)
    with edit_col:
        edit_build = st.button("Edit build")
    with submit_col:
        submit_order = st.button("Submit order", type="primary")

    if edit_build:
        st.session_state["checkout_draft"] = {
            "billing": billing,
            "destination": destination,
            "same_as_billing": same_as_billing,
            "payment_method": payment_method,
            "shipping_choice": shipping_choice,
        }
        st.session_state["flow_step"] = "review"
        st.rerun()

    if submit_order:
        errors = _checkout_errors(billing, shipping)
        if errors:
            st.error(
                "Please fix the following before submitting:\n\n- "
                + "\n- ".join(errors)
            )
        elif not confirmed:
            st.warning("Review the invoice and confirm the order before submitting.")
        else:
            try:
                invoice_num = generate_invoice_number()
                saved_order = {"invoice_num": invoice_num}
                saved_order.update(order_data)
                saved_order["financials"] = {
                    "subtotal": BASE_PRICE,
                    "tax_amount": tax_amount,
                    "shipping_cost": shipping_cost,
                    "total_cost": total_cost,
                }
                create_order(saved_order)
            except (OSError, ValueError) as error:
                st.error(f"Could not save the order: {error}")
            else:
                st.session_state["submitted_invoice"] = format_invoice(
                    order_data,
                    invoice_num,
                    BASE_PRICE,
                    tax_amount,
                    total_cost,
                )
                st.session_state["submitted_invoice_num"] = invoice_num
                st.session_state["flow_step"] = "submitted"
                st.rerun()


st.title("Flammen Rides Unicycles")
st.caption(
    "Customize your build step by step. Billing and shipping are requested "
    "only after you confirm the build."
)

flow_step = st.session_state.setdefault("flow_step", "frame")
if flow_step == "build":
    flow_step = "frame"
    st.session_state["flow_step"] = flow_step

if flow_step == "submitted":
    st.success(f"Order {st.session_state['submitted_invoice_num']} was submitted.")
    st.code(st.session_state["submitted_invoice"], language=None)
    if st.button("Start another order", type="primary"):
        for key in (
            "flow_step",
            "draft_order",
            "checkout_draft",
            "submitted_invoice",
            "submitted_invoice_num",
        ):
            st.session_state.pop(key, None)
        st.rerun()
    st.stop()

steps = {
    "frame": ("1 of 5", 1),
    "saddle": ("2 of 5", 2),
    "drivetrain": ("3 of 5", 3),
    "review": ("4 of 5", 4),
    "checkout": ("5 of 5", 5),
}
if flow_step not in steps:
    st.error(f"Unknown order-flow step: {flow_step}")
    st.stop()
step_label, step_number = steps[flow_step]
st.progress(step_number / 5)
st.caption(f"Step {step_label}")

draft = st.session_state.get("draft_order", {})
if flow_step == "frame":
    section = _render_frame_step(draft)
    if st.button("Continue to saddle & seatpost", type="primary"):
        _save_build(section)
        st.session_state["flow_step"] = "saddle"
        st.rerun()
elif flow_step == "saddle":
    section = _render_saddle_step(draft)
    back_col, continue_col = st.columns(2)
    with back_col:
        back = st.button("Back to frame & tire")
    with continue_col:
        continue_to_drivetrain = st.button(
            "Continue to rim & drivetrain",
            type="primary",
        )
    if back:
        _save_build(section)
        st.session_state["flow_step"] = "frame"
        st.rerun()
    if continue_to_drivetrain:
        _save_build(section)
        st.session_state["flow_step"] = "drivetrain"
        st.rerun()
elif flow_step == "drivetrain":
    section = _render_drivetrain_step(draft)
    back_col, review_col = st.columns(2)
    with back_col:
        back = st.button("Back to saddle & seatpost")
    with review_col:
        review_build = st.button("Review build", type="primary")
    if back:
        _save_build(section)
        st.session_state["flow_step"] = "saddle"
        st.rerun()
    if review_build:
        _save_build(section)
        st.session_state["flow_step"] = "review"
        st.rerun()
elif flow_step == "review":
    _render_build_review(draft)
elif flow_step == "checkout":
    _render_checkout(draft)
