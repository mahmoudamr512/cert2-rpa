from robocorp.tasks import task
from robocorp import browser
from RPA.HTTP import HTTP
import os
from RPA.Tables import Tables
from RPA.PDF import PDF
import shutil


@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    open_robot_order_website()
    orders = get_orders()

    for idx, order in enumerate(orders):
        close_annoying_modal()
        while check_for_error():
            fill_order_form(order)

        pdf_path = save_order_receipt(order)
        screenshot_path = take_screenshot(order)
        embed_screenshot_to_receipt(screenshot_path, pdf_path)

        order_another_robot()

    archive_files()


def check_for_error():
    # check if we are still on the same page that has input fields
    page = browser.page()
    return (
        page.query_selector("input[placeholder='Enter the part number for the legs']")
        is not None
    )


def order_another_robot():
    page = browser.page()
    page.click("button:text('ORDER ANOTHER ROBOT')")


def open_robot_order_website():
    browser.configure(
        screenshot="only-on-failure",
        headless=False,  # won't display the browser window
    )

    browser.goto("https://robotsparebinindustries.com/#/robot-order")


def get_orders():
    http = HTTP()
    http.download(
        "https://robotsparebinindustries.com/orders.csv", "orders.csv", overwrite=True
    )
    library = Tables()
    orders = library.read_table_from_csv(
        "orders.csv", columns=["Order number", "Head", "Body", "Legs", "Address"]
    )
    return orders


def close_annoying_modal():
    page = browser.page()

    page.click("button:text('Yep')")


def fill_order_form(order):
    page = browser.page()
    page.select_option(selector="select[name='head']", value=order["Head"])
    page.check(f"input[name='body'][value='{order['Body']}']")
    page.fill('input[placeholder="Enter the part number for the legs"]', order["Legs"])
    page.fill("#address", order["Address"])
    page.click("button:text('ORDER')")


def save_order_receipt(order):
    page = browser.page()
    page.wait_for_selector("h2:text('Build and order your robot!')")

    receipt = page.inner_html("#receipt")
    pdf = PDF()

    pdf.html_to_pdf(
        receipt,
        f"output/receipts/order_{order['Order number']}.pdf",
    )

    return f"output/receipts/order_{order['Order number']}.pdf"


def take_screenshot(order):
    page = browser.page()
    screenshot = page.screenshot()
    screenshot_path = f"output/images/order_{order['Order number']}.png"
    with open(screenshot_path, "wb") as file:
        file.write(screenshot)
    return screenshot_path


def embed_screenshot_to_receipt(screenshot, pdf_file):
    pdf = PDF()
    pdf.add_files_to_pdf(files=[screenshot], target_document=pdf_file, append=True)


def archive_files():
    shutil.make_archive('output/receipts', 'zip', 'output/receipts')