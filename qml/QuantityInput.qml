import QtQuick 2.5
import QtQuick.Controls 2.2


Rectangle {
    id: root

    width: parent.width

    height: 40

    property string labelText: ""

    property alias from: amount_spnibox.from

    property alias to: amount_spnibox.to

    property alias value: amount_spnibox.value

    Row {
        spacing: 15
        width: parent.width

        Text {
            text: root.labelText
            width: 200
            anchors.verticalCenter: parent.verticalCenter
        }
        SpinBox {
            id: amount_spnibox
            from: 1
            to: 100000
            value: 90
            editable: true
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}