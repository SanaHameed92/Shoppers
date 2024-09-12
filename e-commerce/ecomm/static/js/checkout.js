$(document).ready(function () {
    $(document).off('click', '.payWithRazorpay').on('click', '.payWithRazorpay', function (e) {
        e.preventDefault();
        var selected_address = $("[name='selected_address']").val();
        var payment_method = $("input[name='payment_method']:checked").val();
        var token = $("[name='csrfmiddlewaretoken']").val();

        if (!selected_address) {
            swal("Alert!", "Select the shipping address", "error");
            return false;
        }

        $.ajax({
            method: "POST",
            url: "/products/proceed-to-pay/",
            headers: {
                'X-CSRFToken': token
            },
            data: JSON.stringify({
                selected_address: selected_address,
                payment_method: payment_method
            }),
            contentType: "application/json",
            success: function (response) {
                console.log("Success response:", response);
                var options = {
                    "key": "rzp_test_Yl6grfBbwpSDvh",
                    "amount": response.total_price * 100,
                    "currency": "INR",
                    "name": "Shopper Colorlib",
                    "description": "Thank you for choosing us",
                    "image": "https://example.com/your_logo",
                    "handler": function (responseb) {
                        var data = {
                            "payment_mode": "RazorPay",
                            "selected_address": selected_address,
                            "payment_id": responseb.razorpay_payment_id,
                            "csrfmiddlewaretoken": token,
                            "order_id": response.order_id
                        };
                        console.log("Payment ID:", responseb.razorpay_payment_id);
                        $.ajax({
                            method: "POST",
                            url: "/products/confirm-order-razorpay/",
                            headers: {
                                'X-CSRFToken': token
                            },
                            data: JSON.stringify(data),
                            contentType: "application/json",
                            success: function (responsec) {
                                if (responsec.status === 'Order placed successfully') {
                                    swal("Congratulations!", "Your order has been placed successfully.", "success").then(() => {
                                        window.location.href = '/products/order-success/' + responsec.order_number;
                                    });
                                } else {
                                    swal("Payment Error", responsec.message, "error");
                                }
                            },
                            error: function (xhr, status, error) {
                                console.error("AJAX POST Request Failed:", xhr.responseText);
                            }
                        });
                    },
                    "modal": {
                        "ondismiss": function() {
                            // Handle payment failure here
                            swal("Payment Failed", "The payment could not be processed. Please try again.", "error");
                            window.location.href = '/products/order-failed/';
                        }
                    },
                    "prefill": {
                        "name": response.first_name,
                        "email": response.email,
                        "contact": response.phone_number
                    },
                    "theme": {
                        "color": "#3399cc"
                    }
                };
                var rzp1 = new Razorpay(options);
                rzp1.open();
            },
            error: function (xhr, status, error) {
                console.error("AJAX POST Request Failed:", xhr.responseText);
            }
        });
    });
});
