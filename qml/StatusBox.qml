import QtQuick 2.5
import QtQuick.Controls 2.2


Rectangle {
    id: root
    width: parent.width
    height: 100

    property string imagesLoaded: "0"
    property string failures: "0"

    Column {
        width: parent.width

        InfoText {
        width: parent.width
            id: downloaded_amount_row
            label: "Images downloaded:"
            value: root.imagesLoaded
        }

        InfoText {
        width: parent.width
            id: failures_amount_row
            label: "Failures:"
            value: root.failures
        }
    }
}